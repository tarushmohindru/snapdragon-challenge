"""One deterministic scene image and its already frozen CPU embedding."""
import hashlib
import json
import shutil
import sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parent
CLIP=ROOT.parent/'cliptrail'
sys.path.insert(0,str(CLIP))
from freeze_benchmark import verify_lock
from reference_backend import ClipReference, sha256


def main():
    destination=ROOT/'bundle/input'
    if (destination/'reference.json').exists():
        old=json.loads((destination/'reference.json').read_text())
        for name,h in old['file_sha256'].items():
            assert sha256(destination/name)==h,name
        print('Existing fixed reference verified; no inference repeated.')
        return
    manifest,lock=verify_lock(CLIP/'datasets/real-v1/manifest.json')
    report=json.loads((CLIP/'results/real-v1/report.json').read_text())
    scene=next(r for r in report['rows'] if r['method']=='scene')
    clip=next(c for c in manifest['clips'] if c['id']==scene['clip_id'])
    index=scene['selected_indices'][0]
    frame=clip['frames'][index]
    source=CLIP/'datasets/real-v1'/frame['path']
    assert sha256(source)==frame['sha256']
    offset=scene['image_embedding_byte_offsets'][str(index)]
    with (CLIP/'results/real-v1'/scene['embedding_file']).open('rb') as f:
        f.seek(offset)
        expected=np.frombuffer(f.read(512*4),dtype='<f4').copy().reshape(1,512)
    model=ClipReference(CLIP/'assets/model',CLIP/'results/provisioning.json',2)
    actual,cost=model.encode_image(source)
    actual=np.asarray(actual,dtype='float32').reshape(1,512)
    np.testing.assert_allclose(actual,expected,rtol=1e-5,atol=1e-6)
    with Image.open(source) as image:
        raw=model.processor(images=image.convert('RGB'),do_normalize=False,return_tensors='np')['pixel_values']
        normalized=model.processor(images=image.convert('RGB'),return_tensors='np')['pixel_values']
    assert raw.shape==normalized.shape==(1,3,224,224)
    assert raw.min()>=0 and raw.max()<=1
    destination.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,destination/'scene.jpg')
    for name,array in [('image_raw_nchw',raw),('image_normalized_nchw',normalized),('cpu_reference',expected)]:
        np.save(destination/(name+'.npy'),array,allow_pickle=False)
    meta={'selection_rule':'First selected frame of first frozen scene-method row; no quality-based selection',
          'clip_id':clip['id'],'frame_index':index,'timestamp_s':frame['t_s'],
          'source_timestamp_s':frame['source_t_s'],'image_source':frame['path'],
          'attribution':clip['attribution'],'video_source_url':clip['source_url'],
          'frame_sha256':frame['sha256'],
          'frozen_report_sha256':sha256(CLIP/'results/real-v1/report.json'),
          'frozen_embedding_file_sha256':sha256(CLIP/'results/real-v1'/scene['embedding_file']),
          'embedding_byte_offset':offset,'cpu_reference_model':model.metadata,
          'fresh_reference_replay':{'max_absolute_error':float(np.abs(actual-expected).max()),'cost':cost},
          'preprocessing':'Frozen Transformers CLIPImageProcessor RGB bicubic resize/center crop; raw RGB float32 [0,1] in NCHW. Qualcomm wrapper normalizes internally. Normalized tensor also saved for explicit export fallback.',
          'file_sha256':{p.name:sha256(p) for p in sorted(destination.iterdir()) if p.is_file()},
          'npu_verified':False}
    (destination/'reference.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps({k:meta[k] for k in ('clip_id','frame_index','timestamp_s','fresh_reference_replay')}))


if __name__=='__main__': main()
