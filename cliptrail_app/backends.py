"""Image/text embedding backends behind one application interface."""
import hashlib
import json
import math
import os
from pathlib import Path
import platform
from typing import Protocol

from .legacy import ClipReference, sha256

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = ROOT / 'experiments/cliptrail/assets/model'
DEFAULT_PROVISIONING = ROOT / 'experiments/cliptrail/results/provisioning.json'
DEFAULT_QNN_BUNDLE = ROOT / 'experiments/cliptrail_target/bundle'
DIMENSIONS = 512


def normalized_vector(values):
    values = tuple(float(x) for x in values)
    if len(values) != DIMENSIONS or not all(math.isfinite(x) for x in values):
        raise ValueError('Expected finite 512-dimensional CLIP embedding')
    norm = math.sqrt(sum(x * x for x in values))
    if not .98 <= norm <= 1.02:
        raise ValueError(f'Expected unit CLIP embedding; norm={norm}')
    return values


class EmbeddingBackend(Protocol):
    identity: str
    label: str

    def encode_image(self, path: Path) -> tuple: ...
    def encode_text(self, text: str) -> tuple: ...


class CpuClipBackend:
    """Application adapter over the measured offline PyTorch/Transformers code."""

    label = 'CPU CLIP ViT-B/16'

    def __init__(self, model_dir=DEFAULT_MODEL, provisioning=DEFAULT_PROVISIONING, threads=2):
        self.reference = ClipReference(model_dir, provisioning, threads)
        model = self.reference.metadata
        key = {'kind': 'cpu_clip', 'revision': model['revision'],
               'asset_sha256': model['asset_sha256'],
               'processor_sha256': sha256(Path(model_dir) / 'preprocessor_config.json')}
        self.identity = 'cpu:' + hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:24]

    def encode_image(self, path):
        vector, _cost = self.reference.encode_image(path)
        return normalized_vector(vector)

    def encode_text(self, text):
        vector, _cost = self.reference.encode_text(text)
        return normalized_vector(vector)


class QnnClipBackend:
    """Experimental QNN image graph with the same CPU CLIP text tower.

    It uses the issued image graph and strict no-fallback policy. The host Python
    environment must also provide PyTorch/Transformers for the text encoder.
    The v2 target evidence does not establish stable shutdown or NPU hardware work.
    """

    label = 'QNN image graph + CPU CLIP text (experimental; NPU unverified)'

    def __init__(self, model_dir=DEFAULT_MODEL, provisioning=DEFAULT_PROVISIONING,
                 bundle=DEFAULT_QNN_BUNDLE, threads=2):
        if platform.system() != 'Windows' or platform.machine().upper() not in {'ARM64', 'AARCH64'}:
            raise RuntimeError('The issued QNN image graph requires native Windows ARM64')
        self.text = CpuClipBackend(model_dir, provisioning, threads)
        import numpy as np
        import onnxruntime as ort
        import onnxruntime_qnn as qnn
        bundle = Path(bundle).resolve()
        manifest = json.loads((bundle / 'bundle-manifest.json').read_text())
        graph = bundle / 'model/image_encoder.onnx'
        htp = bundle / manifest['runtime']['htp_backend']
        if sha256(graph) != manifest['model']['sha256'] or sha256(htp) != manifest['runtime']['htp_sha256']:
            raise ValueError('QNN graph or backend differs from issued manifest')
        if qnn.__version__ != manifest['runtime']['qnn_version']:
            raise ValueError('QNN plugin version differs from issued runtime')
        self._capi_cookie = os.add_dll_directory(str(bundle / manifest['runtime']['capi_directory']))
        self._qnn_cookie = os.add_dll_directory(str(bundle / manifest['runtime']['qnn_directory']))
        library = Path(qnn.get_library_path()).resolve()
        if sha256(library) != manifest['runtime']['ep_sha256']:
            raise ValueError('QNN provider DLL differs from issued runtime')
        ort.register_execution_provider_library('QNNExecutionProvider', str(library))
        devices = [d for d in ort.get_ep_devices()
                   if d.ep_name == 'QNNExecutionProvider' and d.device.type == ort.OrtHardwareDeviceType.NPU]
        if len(devices) != 1:
            raise RuntimeError('Expected exactly one QNN NPU device')
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 2
        opts.inter_op_num_threads = 1
        opts.add_session_config_entry('session.disable_cpu_ep_fallback', '1')
        opts.add_provider_for_devices(devices, {
            'backend_path': str(htp), 'offload_graph_io_quantization': '0',
            'enable_htp_fp16_precision': '1', 'htp_performance_mode': 'balanced',
        })
        self.session = ort.InferenceSession(str(graph), sess_options=opts, enable_fallback=False)
        self.session.disable_fallback()
        if 'QNNExecutionProvider' not in self.session.get_providers():
            raise RuntimeError('QNN provider not active')
        self._np = np
        self.identity = f'qnn:{manifest["model"]["sha256"][:24]}:text:{self.text.identity}'

    def encode_image(self, path):
        from PIL import Image
        with Image.open(path) as image:
            raw = self.text.reference.processor(
                images=image.convert('RGB'), do_normalize=False, return_tensors='np')['pixel_values']
        raw = self._np.asarray(raw, dtype=self._np.float32)
        if raw.shape != (1, 3, 224, 224):
            raise ValueError('Unexpected QNN image input shape')
        result = self.session.run(['image_features'], {'image': raw})[0]
        if result.shape != (1, DIMENSIONS):
            raise ValueError('Unexpected QNN output shape')
        return normalized_vector(result[0])

    def encode_text(self, text):
        return self.text.encode_text(text)


def make_backend(name='cpu', **kwargs):
    if name == 'cpu':
        return CpuClipBackend(**kwargs)
    if name == 'qnn':
        return QnnClipBackend(**kwargs)
    raise ValueError(f'Unknown inference backend: {name}')
