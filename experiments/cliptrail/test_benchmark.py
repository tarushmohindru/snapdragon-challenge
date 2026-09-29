"""Correctness tests only. These are not model/retrieval evidence."""
import copy
import tempfile
import unittest
from pathlib import Path
from benchmark_core import METHODS, aggregate, evaluate_query, gate, static_selection, summarize
from freeze_benchmark import validate
from run_benchmark import run_case


class MetricTests(unittest.TestCase):
    def test_half_open_intervals_and_all_occurrences(self):
        v = evaluate_query([12.0, 7.0, 2.0], [2.0, 7.0, 12.0], [[2, 3], [10, 12]])
        self.assertEqual((v['recall_at_1'], v['recall_at_3'], v['coverage']), (0, 1, 1))
        self.assertEqual(v['localization_error_s'], 0)  # at open right boundary
        self.assertTrue(v['short_event'])

    def test_localization_counts_failed_queries(self):
        rows = [{'metrics': evaluate_query([t], [t], [[10, 11]])} for t in (10.5, 20)]
        v = aggregate(rows)
        self.assertEqual(v['recall_at_1'], .5)
        self.assertEqual(v['localization_error_s_median'], 4.5)

    def test_mixed_event_lengths_are_not_short(self):
        self.assertFalse(evaluate_query([1], [1], [[1, 2], [4, 8]])['short_event'])

    def test_equal_quality_kills_adaptive_even_if_all_are_useful(self):
        rows = [{'method': m, 'clip_id': c, 'source_id': c, 'query_id': c,
                 'metrics': evaluate_query([1], [1], [[1, 2]])}
                for c in ('a', 'b') for m in METHODS]
        verdict = gate(summarize(rows))
        self.assertEqual(verdict['adaptive_verdict'], 'kill_adaptive_v1')
        self.assertEqual(len(verdict['simple_usefulness_gate_passes']), 4)


class SelectionTests(unittest.TestCase):
    def test_static_budget_cardinality_and_range(self):
        for n in (1, 2, 3, 17, 240):
            for b in (1, 2, 8, 16, 32):
                for method in METHODS[:-1]:
                    selected = static_selection(method, [0.1] * n, b)
                    self.assertEqual(len(selected), min(n, b))
                    self.assertEqual(len(set(selected)), len(selected))
                    self.assertTrue(all(0 <= i < n for i in selected))

    def test_real_runner_charges_refinement_and_text(self):
        # Counting test double; no CLI mock mode and no benchmark artifacts.
        class CountingBackend:
            image_calls = text_calls = 0
            def encode_image(self, path):
                self.image_calls += 1
                return [1.] + [0.] * 511, {'total_ms': 0}
            def encode_text(self, text):
                self.text_calls += 1
                return [1.] + [0.] * 511, {'total_ms': 0}
        frames = [{'path': f'{i}.jpg', 't_s': i / 4, 'change': .1} for i in range(240)]
        with tempfile.TemporaryDirectory() as folder:
            for method in METHODS:
                backend = CountingBackend()
                row, vectors, _ = run_case(backend, frames, 'counting test', method, 16, Path(folder))
                self.assertEqual((backend.image_calls, backend.text_calls), (16, 1))
                self.assertEqual(len(vectors), 16)
                self.assertEqual(row['cost']['query_image_calls'], 8 if method == 'hierarchical' else 0)


class AnnotationTests(unittest.TestCase):
    def corpus(self):
        clips = []
        for c in range(6):
            clips.append({'id': f'c{c}', 'source_id': f's{c%2}', 'duration_s': 40,
                          'selection_reason': 'fixture', 'source_url': 'https://example.org',
                          'attribution': 'test', 'video_sha256': str(c%2),
                          'start_s': (c//2)*40,
                          'frames': [{'path': f'{c}/{i}.jpg', 't_s': i/4, 'change': .1} for i in range(160)],
                          'queries': [{'id': f'q{c}_{q}', 'text': f'fixture {q}', 'rationale': 'fixture',
                                       'confounders': 'fixture', 'intervals_s': [[q*3, q*3+1]]} for q in range(4)]})
        return {'schema': 2, 'grid_hz': 4, 'annotator': 'test-only',
                'annotations_before_model_results': True, 'all_matching_occurrences_reviewed': True,
                'clips': clips}

    def test_reject_unreviewed_annotations(self):
        data = self.corpus()
        data['all_matching_occurrences_reviewed'] = False
        with self.assertRaisesRegex(ValueError, 'matching occurrences'):
            validate(data, Path('/tmp'), verify_images=False)

    def test_reject_invented_or_missing_temporal_ground_truth(self):
        for interval in ([[41, 42]], [], [[0, .1]]):
            data = self.corpus()
            data['clips'][0]['queries'][0]['intervals_s'] = interval
            with self.assertRaises(ValueError):
                validate(data, Path('/tmp'), verify_images=False)

    def test_valid_fixture_has_minimum_counts(self):
        result = validate(self.corpus(), Path('/tmp'), verify_images=False)
        self.assertEqual((result['clips'], result['queries'], result['short_queries']), (6, 24, 24))


if __name__ == '__main__':
    unittest.main()
