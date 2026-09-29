"""Transactional local SQLite index of scene embeddings and preview images."""
from pathlib import Path
import sqlite3
import struct

from . import APP_SCHEMA, SAMPLER_ID
from .backends import DIMENSIONS, normalized_vector

VECTOR = struct.Struct('<512f')


class IndexStore:
    def __init__(self, path):
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute('PRAGMA foreign_keys=ON')
        self.connection.execute('PRAGMA journal_mode=WAL')
        self.connection.executescript('''
            CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY, path TEXT NOT NULL, filename TEXT NOT NULL,
                source_sha256 TEXT NOT NULL, source_bytes INTEGER NOT NULL,
                backend_identity TEXT NOT NULL, sampler_id TEXT NOT NULL,
                duration_s REAL NOT NULL, decoded_frames INTEGER NOT NULL,
                candidate_frames INTEGER NOT NULL, selected_frames INTEGER NOT NULL,
                index_elapsed_s REAL NOT NULL, logical_storage_bytes INTEGER NOT NULL,
                indexed_utc TEXT NOT NULL,
                UNIQUE(path, backend_identity)
            );
            CREATE TABLE IF NOT EXISTS frames (
                id INTEGER PRIMARY KEY, video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
                ordinal INTEGER NOT NULL, timestamp_s REAL NOT NULL, source_pts INTEGER NOT NULL,
                embedding BLOB NOT NULL, thumbnail BLOB NOT NULL,
                UNIQUE(video_id, ordinal)
            );
            CREATE INDEX IF NOT EXISTS frames_video ON frames(video_id);
        ''')
        current = self.connection.execute('SELECT value FROM settings WHERE key="schema"').fetchone()
        if current and int(current['value']) != APP_SCHEMA:
            raise ValueError('Index schema differs from this ClipTrail version')
        self.connection.execute('INSERT OR IGNORE INTO settings(key,value) VALUES (?,?)', ('schema', str(APP_SCHEMA)))
        self.connection.commit()

    def close(self):
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def current(self, path, backend_identity, source_sha256):
        row = self.connection.execute('''
            SELECT id FROM videos WHERE path=? AND backend_identity=?
              AND source_sha256=? AND sampler_id=?
        ''', (str(Path(path).resolve()), backend_identity, source_sha256, SAMPLER_ID)).fetchone()
        return row is not None

    def replace_video(self, *, path, source_sha256, source_bytes, backend_identity,
                      duration_s, decoded_frames, candidate_frames, index_elapsed_s,
                      frames, indexed_utc):
        if duration_s <= 0 or not frames:
            raise ValueError('Cannot persist an empty video index')
        packed = []
        for ordinal, (timestamp_s, pts, vector, thumbnail) in enumerate(frames):
            if timestamp_s < 0 or not thumbnail:
                raise ValueError('Invalid selected frame')
            blob = VECTOR.pack(*normalized_vector(vector))
            packed.append((ordinal, float(timestamp_s), int(pts), blob, bytes(thumbnail)))
        logical_bytes = sum(len(v) + len(t) for _, _, _, v, t in packed)
        absolute = str(Path(path).resolve())
        # Delete/insert is one transaction: a failure preserves the previous index.
        with self.connection:
            self.connection.execute('DELETE FROM videos WHERE path=? AND backend_identity=?',
                                    (absolute, backend_identity))
            cursor = self.connection.execute('''
                INSERT INTO videos(path,filename,source_sha256,source_bytes,backend_identity,
                    sampler_id,duration_s,decoded_frames,candidate_frames,selected_frames,
                    index_elapsed_s,logical_storage_bytes,indexed_utc)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (absolute, Path(path).name, source_sha256, source_bytes, backend_identity,
                  SAMPLER_ID, duration_s, decoded_frames, candidate_frames, len(packed),
                  index_elapsed_s, logical_bytes, indexed_utc))
            video_id = cursor.lastrowid
            self.connection.executemany('''
                INSERT INTO frames(video_id,ordinal,timestamp_s,source_pts,embedding,thumbnail)
                VALUES (?,?,?,?,?,?)
            ''', [(video_id, *row) for row in packed])
        return video_id, logical_bytes

    def vectors(self, backend_identity):
        for row in self.connection.execute('''
            SELECT f.id AS result_id, f.timestamp_s, f.embedding, v.path, v.filename
            FROM frames f JOIN videos v ON v.id=f.video_id
            WHERE v.backend_identity=? AND v.sampler_id=?
            ORDER BY v.path, f.timestamp_s, f.id
        ''', (backend_identity, SAMPLER_ID)):
            yield {'result_id': row['result_id'], 'timestamp_s': row['timestamp_s'],
                   'vector': VECTOR.unpack(row['embedding']),
                   'path': row['path'], 'filename': row['filename']}

    def result(self, result_id):
        row = self.connection.execute('''
            SELECT f.id, f.timestamp_s, f.thumbnail, v.path, v.filename, v.backend_identity
            FROM frames f JOIN videos v ON v.id=f.video_id WHERE f.id=?
        ''', (result_id,)).fetchone()
        return dict(row) if row else None

    def materialize_thumbnail(self, result_id):
        row = self.result(result_id)
        if row is None:
            raise KeyError(f'Unknown result ID: {result_id}')
        preview = self.path.parent / 'thumbnails' / f'{result_id}.jpg'
        if not preview.exists() or preview.read_bytes() != row['thumbnail']:
            preview.parent.mkdir(parents=True, exist_ok=True)
            temp = preview.with_suffix('.jpg.tmp')
            temp.write_bytes(row['thumbnail'])
            temp.replace(preview)
        return preview

    def videos(self):
        return [dict(row) for row in self.connection.execute('''
            SELECT *, ROUND(index_elapsed_s / (duration_s / 60.0), 3) AS index_s_per_video_min,
                   ROUND(logical_storage_bytes / (duration_s / 60.0), 1) AS logical_bytes_per_video_min
            FROM videos ORDER BY path, backend_identity
        ''')]

    def disk_bytes(self):
        paths = [self.path, self.path.with_name(self.path.name + '-wal'),
                 self.path.with_name(self.path.name + '-shm')]
        return sum(p.stat().st_size for p in paths if p.exists())
