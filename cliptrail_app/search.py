"""Natural language retrieval over a persistent index."""
import time

from .backends import normalized_vector
from .legacy import cosine


def rank_vectors(rows, text_vector, limit=5):
    if limit < 1:
        raise ValueError('limit must be positive')
    query = normalized_vector(text_vector)
    ranked = []
    for row in rows:
        vector = normalized_vector(row['vector'])
        ranked.append({k: v for k, v in row.items() if k != 'vector'} | {
            'similarity': cosine(vector, query)})
    return sorted(ranked, key=lambda r: (-r['similarity'], r['timestamp_s'], r['path'],
                                          r.get('result_id', 0)))[:limit]


def search(store, backend, text, limit=5, *, materialize_thumbnails=True):
    if not text.strip():
        raise ValueError('Search text cannot be empty')
    began = time.perf_counter()
    vector = backend.encode_text(text)
    encoded = time.perf_counter()
    ranked = rank_vectors(store.vectors(backend.identity), vector, limit)
    if materialize_thumbnails:
        for item in ranked:
            item['thumbnail'] = str(store.materialize_thumbnail(item['result_id']))
    finished = time.perf_counter()
    return ranked, {'text_encode_ms': (encoded - began) * 1000,
                    'ranking_and_thumbnail_ms': (finished - encoded) * 1000,
                    'query_ms': (finished - began) * 1000,
                    'indexed_frames': sum(v['selected_frames'] for v in store.videos()
                                          if v['backend_identity'] == backend.identity)}
