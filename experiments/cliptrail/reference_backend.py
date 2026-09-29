"""Offline OpenAI ViT-B/16 reference adapter. No QNN claim or mock fallback."""
import hashlib
import json
import os
import platform
import time
from pathlib import Path


def sha256(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def cosine(a, b):
    if len(a) != 512 or len(b) != 512:
        raise ValueError('Expected normalized 512D CLIP vectors')
    return sum(x * y for x, y in zip(a, b))


class ClipReference:
    def __init__(self, model_dir, provisioning, threads=2):
        start = time.perf_counter()
        model_dir = Path(model_dir).resolve()
        source = json.loads(Path(provisioning).read_text())['model']
        if source.get('repo_id') != 'openai/clip-vit-base-patch16' or not source.get('revision'):
            raise ValueError('Missing official checkpoint revision/provenance')
        if not source.get('files') or source.get('weight_file') not in source['files']:
            raise ValueError('Missing weight hash in provisioning manifest')
        for name, info in source['files'].items():
            if Path(name).name != name or sha256(model_dir / name) != info['sha256']:
                raise ValueError(f'Asset provenance/hash mismatch: {name}')
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        os.environ['TOKENIZERS_PARALLELISM'] = 'false'
        import torch
        import transformers
        from transformers import CLIPImageProcessor, CLIPModel, CLIPTokenizerFast
        if threads < 1:
            raise ValueError('threads must be positive')
        torch.set_num_threads(threads)
        torch.set_num_interop_threads(1)
        torch.manual_seed(0)
        self.torch = torch
        self.model = CLIPModel.from_pretrained(
            str(model_dir), local_files_only=True, torch_dtype=torch.float32,
        ).to('cpu').eval()
        config = self.model.config
        vision, text = config.vision_config, config.text_config
        if (vision.patch_size, vision.hidden_size, vision.num_hidden_layers,
            vision.num_attention_heads, vision.image_size, config.projection_dim) != (16, 768, 12, 12, 224, 512):
            raise ValueError('Checkpoint is not the expected CLIP ViT-B/16 image tower')
        if (text.hidden_size, text.num_hidden_layers, text.max_position_embeddings,
            text.vocab_size) != (512, 12, 77, 49408):
            raise ValueError('Unexpected CLIP text tower')
        self.processor = CLIPImageProcessor.from_pretrained(str(model_dir), local_files_only=True)
        self.tokenizer = CLIPTokenizerFast.from_pretrained(str(model_dir), local_files_only=True)
        self.image_calls = self.text_calls = 0
        self.metadata = {
            'model': source['repo_id'], 'revision': source['revision'],
            'asset_sha256': {k: v['sha256'] for k, v in source['files'].items()},
            'runtime': 'Transformers CLIPModel / PyTorch CPU float32',
            'torch': torch.__version__, 'transformers': transformers.__version__,
            'python': platform.python_version(), 'platform': platform.platform(),
            'threads': threads, 'logical_cpus': os.cpu_count(),
            'init_and_verification_ms': (time.perf_counter() - start) * 1000,
            'image_processor': self.processor.to_dict(),
            'npu_verified': False,
        }

    def _vector(self, output):
        vector = output.float()
        if vector.shape != (1, 512) or not self.torch.isfinite(vector).all():
            raise RuntimeError('Invalid model output; expected finite [1,512] embedding')
        norm = vector.norm(dim=-1, keepdim=True)
        if norm.item() <= 0:
            raise RuntimeError('Zero model embedding')
        return (vector / norm)[0].tolist()

    def encode_image(self, path):
        from PIL import Image
        start = time.perf_counter()
        with Image.open(path) as image:
            inputs = self.processor(images=image.convert('RGB'), return_tensors='pt')
        pre_end = time.perf_counter()
        with self.torch.inference_mode():
            result = self._vector(self.model.get_image_features(**inputs))
        end = time.perf_counter()
        self.image_calls += 1
        return result, {'preprocess_ms': (pre_end - start) * 1000,
                        'forward_normalize_ms': (end - pre_end) * 1000,
                        'total_ms': (end - start) * 1000}

    def encode_text(self, query):
        start = time.perf_counter()
        inputs = self.tokenizer([query], return_tensors='pt', padding=True, truncation=False)
        if inputs['input_ids'].shape[1] > 77:
            raise ValueError('Query exceeds 77 CLIP tokens; refusing silent truncation')
        pre_end = time.perf_counter()
        with self.torch.inference_mode():
            result = self._vector(self.model.get_text_features(**inputs))
        end = time.perf_counter()
        self.text_calls += 1
        return result, {'preprocess_ms': (pre_end - start) * 1000,
                        'forward_normalize_ms': (end - pre_end) * 1000,
                        'total_ms': (end - start) * 1000}

    def warmup(self, path):
        _, image_cost = self.encode_image(path)
        _, text_cost = self.encode_text('a photograph of an object')
        self.metadata['warmup'] = {'image_calls': 1, 'text_calls': 1,
                                   'image': image_cost, 'text': text_cost}
        self.image_calls = self.text_calls = 0
