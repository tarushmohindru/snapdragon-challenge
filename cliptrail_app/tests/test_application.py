"""Application invariants and a real decode/persist/query flow; no model rerun."""
import json
import math
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock

from cliptrail_app.backends import normalized_vector
from cliptrail_app.indexer import index_video
from cliptrail_app.legacy import scene_indices
from cliptrail_app.playback import open_result, player_command
from cliptrail_app.search import rank_vectors, search
from cliptrail_app.store import IndexStore
from cliptrail_app.video import Candidate, discover, scan, select_candidates


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = ROOT / 'experiments/cliptrail'


class SimpleBackend:
    identity = 'test:color-v1'
    label = 'test fixture only'

    def encode_image(self, path):
        from PIL import Image
        with Image.open(path) as image:
            pixel = image.convert('RGB').resize((1, 1)).getpixel((0, 0))
        return tuple([1.0, 0.0] if pixel[0] >= pixel[2] else [0.0, 1.0]) + (0.0,) * 510

    def encode_text(self, text):
        return tuple([1.0, 0.0] if text == 'red' else [0.0, 1.0]) + (0.0,) * 510


def write_video(path):
    import av
    import numpy as np
    with av.open(str(path), mode='w') as out:
        stream = out.add_stream('mpeg4', rate=4)
        stream.width = 64
        stream.height = 48
        stream.pix_fmt = 'yuv420p'
        for i in range(48):
            rgb = np.zeros((48, 64, 3), dtype=np.uint8)
            rgb[:, :, 0 if i < 24 else 2] = 240
            out.mux(stream.encode(av.VideoFrame.from_ndarray(rgb, format='rgb24')))
        out.mux(stream.encode(None))


class ApplicationTests(unittest.TestCase):
    def test_scene_selection_matches_frozen_rule_and_keeps_actual_times(self):
        frames = [Candidate(i, i / 4, 0.9 if i == 20 else 0.0, 0) for i in range(48)]
        selected = select_candidates(frames)
        self.assertEqual([f.pts for f in selected], scene_indices([f.change for f in frames], 16))
        self.assertEqual([f.t_s for f in selected], [f.pts / 4 for f in selected])
        self.assertEqual(len(selected), 16)

    def test_vector_validation_and_stable_ranking(self):
        with self.assertRaises(ValueError): normalized_vector([1.0] * 511)
        with self.assertRaises(ValueError): normalized_vector([math.nan] + [0.0] * 511)
        with self.assertRaises(ValueError): normalized_vector([0.0] * 512)
        red = (1.0, 0.0) + (0.0,) * 510
        blue = (0.0, 1.0) + (0.0,) * 510
        rows = [dict(vector=red, timestamp_s=5.0, path='/b', result_id=2),
                dict(vector=blue, timestamp_s=1.0, path='/a', result_id=3),
                dict(vector=red, timestamp_s=2.0, path='/a', result_id=1)]
        self.assertEqual([r['result_id'] for r in rank_vectors(rows, red)], [1, 2, 3])

    def test_decode_persist_query_reopen_and_failed_replace(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / 'two-scenes.mp4'
            write_video(video)
            candidates, duration, decoded = scan(video)
            self.assertEqual(len(candidates), 48)
            self.assertEqual(candidates[0].change, 0.0)
            self.assertGreater(candidates[24].change, 0.5)
            self.assertGreaterEqual(duration, 12)
            self.assertEqual(decoded, 48)
            db = root / 'index.sqlite3'
            backend = SimpleBackend()
            with IndexStore(db) as store:
                outcome = index_video(store, backend, video)
                self.assertEqual(outcome['selected_frames'], 16)
                self.assertEqual(index_video(store, backend, video)['status'], 'cached')
                original = list(store.vectors(backend.identity))
                self.assertEqual(len(original), 16)
                with self.assertRaises(Exception):
                    store.replace_video(path=video, source_sha256='bad', source_bytes=1,
                        backend_identity=backend.identity, duration_s=12, decoded_frames=48,
                        candidate_frames=48, index_elapsed_s=1, indexed_utc=None,
                        frames=[(0.0, 0, backend.encode_text('red'), b'jpg')])
                self.assertEqual(list(store.vectors(backend.identity)), original)
            with IndexStore(db) as store:
                results, timing = search(store, backend, 'red', 5)
                self.assertEqual(len(results), 5)
                self.assertEqual(results[0]['similarity'], 1.0)
                self.assertTrue(Path(results[0]['thumbnail']).is_file())
                self.assertEqual(results[0]['timestamp_s'], store.result(results[0]['result_id'])['timestamp_s'])
                self.assertEqual(timing['indexed_frames'], 16)
                player = root / 'mpv'
                player.write_text('#!/bin/sh\nexit 0\n')
                player.chmod(0o755)
                cmd = player_command(store.result(results[0]['result_id'])['path'],
                                     results[0]['timestamp_s'], str(player))
                self.assertEqual(cmd[-1], str(video))
                self.assertEqual(cmd[1], f'--start={results[0]["timestamp_s"]:.3f}')
                with mock.patch('cliptrail_app.playback.subprocess.Popen') as launched:
                    launched.return_value.pid = 123
                    opened = open_result(store, results[0]['result_id'], str(player))
                    self.assertEqual(opened['timestamp_s'], results[0]['timestamp_s'])
                    self.assertEqual(launched.call_args.args[0], cmd)
                with mock.patch('cliptrail_app.playback.webbrowser.open', return_value=False):
                    opened = open_result(store, results[0]['result_id'], 'browser')
                viewer = Path(opened['viewer'])
                self.assertTrue(viewer.is_file())
                self.assertIn(f'video.currentTime={results[0]["timestamp_s"]:.6f}', viewer.read_text())
                self.assertIn(video.as_uri(), viewer.read_text())
                self.assertFalse(opened['browser_launched'])

    def test_folder_discovery_and_indexing_two_videos(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / 'library'
            folder.mkdir()
            first = folder / 'a.mp4'
            second = folder / 'sub' / 'b.mp4'
            second.parent.mkdir()
            write_video(first)
            write_video(second)
            self.assertEqual(discover(folder), [first, second])
            with IndexStore(root / 'library.sqlite3') as store:
                for path in discover(folder):
                    index_video(store, SimpleBackend(), path)
                self.assertEqual(len(store.videos()), 2)
                results, _ = search(store, SimpleBackend(), 'red', 40)
                self.assertEqual({r['filename'] for r in results}, {'a.mp4', 'b.mp4'})

    def test_frozen_scene_quality_replays_unchanged_without_inference(self):
        from benchmark_core import evaluate_query
        manifest = json.loads((EXPERIMENT / 'datasets/real-v1/manifest.json').read_text())
        report_dir = EXPERIMENT / 'results/real-v1-amended'
        report = json.loads((report_dir / 'report.json').read_text())
        clips = {clip['id']: clip for clip in manifest['clips']}
        rows = [row for row in report['rows'] if row['method'] == 'scene']
        self.assertEqual(len(rows), 24)
        recalled_1 = recalled_3 = short_3 = short_count = 0
        with (report_dir / 'embeddings.f32').open('rb') as embeddings:
            def read(offset):
                embeddings.seek(offset)
                return struct.unpack('<512f', embeddings.read(512 * 4))
            for row in rows:
                frames = clips[row['clip_id']]['frames']
                selected = scene_indices([f['change'] for f in frames], 16)
                self.assertEqual(selected, row['selected_indices'])
                text = read(row['text_embedding_byte_offset'])
                vectors = [dict(vector=read(row['image_embedding_byte_offsets'][str(i)]),
                                timestamp_s=frames[i]['t_s'], path=row['clip_id'], result_id=i)
                           for i in selected]
                ranking = rank_vectors(vectors, text, 16)
                self.assertEqual([r['result_id'] for r in ranking], row['ranked_indices'])
                self.assertEqual([r['timestamp_s'] for r in ranking], row['ranked_times_s'])
                metrics = evaluate_query([r['timestamp_s'] for r in ranking],
                                         [frames[i]['t_s'] for i in selected], row['intervals_s'])
                self.assertEqual(metrics, row['metrics'])
                recalled_1 += metrics['recall_at_1']
                recalled_3 += metrics['recall_at_3']
                if metrics['short_event']:
                    short_count += 1
                    short_3 += metrics['recall_at_3']
        self.assertEqual((recalled_1, recalled_3, short_count, short_3), (20, 21, 11, 9))
