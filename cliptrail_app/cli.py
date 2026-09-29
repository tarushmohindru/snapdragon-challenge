"""Local CLI: index, search, open, status and metrics."""
import argparse
import json
from pathlib import Path
import sys

from .backends import make_backend
from .indexer import index_video
from .playback import open_result
from .search import search
from .store import IndexStore
from .video import discover

DEFAULT_DB = Path('.cliptrail/index.sqlite3')


def parser():
    p = argparse.ArgumentParser(prog='cliptrail', description='Local scene-indexed video search')
    p.add_argument('--db', type=Path, default=DEFAULT_DB, help='SQLite index path (default .cliptrail/index.sqlite3)')
    sub = p.add_subparsers(dest='command', required=True)
    index = sub.add_parser('index', help='Index one video or a directory recursively')
    index.add_argument('source', type=Path)
    index.add_argument('--backend', choices=('cpu', 'qnn'), default='cpu')
    index.add_argument('--force', action='store_true', help='Rebuild even when source hash matches')
    query = sub.add_parser('search', help='Search a prebuilt index using CLIP text')
    query.add_argument('text')
    query.add_argument('--backend', choices=('cpu', 'qnn'), default='cpu')
    query.add_argument('--limit', type=int, default=5)
    query.add_argument('--json', action='store_true')
    query.add_argument('--open', type=int, metavar='RANK', help='Open this numbered result after search')
    query.add_argument('--player', help='browser, mpv, ffplay, vlc or explicit executable path')
    open_cmd = sub.add_parser('open', help='Open a prior result ID at its timestamp')
    open_cmd.add_argument('result_id', type=int)
    open_cmd.add_argument('--player', help='browser, mpv, ffplay, vlc or explicit executable path')
    sub.add_parser('status', help='List indexed videos and current stored metrics')
    sub.add_parser('metrics', help='Show per-video indexing metrics and total index disk size')
    serve = sub.add_parser('serve', help='Run the persistent local browser application')
    serve.add_argument('--backend', choices=('cpu', 'qnn'), default='cpu')
    serve.add_argument('--port', type=int, default=8765)
    serve.add_argument('--no-browser', action='store_true')
    return p


def print_json(value):
    print(json.dumps(value, indent=2, allow_nan=False))


def main(argv=None, backend_factory=make_backend):
    args = parser().parse_args(argv)
    if args.command == 'serve':
        from .web import run_server
        run_server(args.db, args.backend, args.port, not args.no_browser, backend_factory)
        return 0
    with IndexStore(args.db) as store:
        if args.command == 'index':
            videos = discover(args.source)
            print(f'Found {len(videos)} video(s); loading {args.backend} backend locally…', file=sys.stderr)
            backend = backend_factory(args.backend)
            outcomes = []
            errors = []
            for number, path in enumerate(videos, 1):
                print(f'[{number}/{len(videos)}] {path.name}: starting', file=sys.stderr)
                last = {'embed': -1, 'decode': -1, 'extract': -1}

                def progress(stage, count, value, duration):
                    if stage == 'cached':
                        print(f'  cached; source and model unchanged', file=sys.stderr)
                    elif stage == 'decode' and (count - last['decode'] >= 32 or value == duration):
                        last['decode'] = count
                        print(f'  decoded {count} candidate frames; at {value:.1f}s', file=sys.stderr)
                    elif stage in {'embed', 'extract'} and (count - last[stage] >= 4 or count == value):
                        last[stage] = count
                        print(f'  {stage} {count}/{value}', file=sys.stderr)

                try:
                    result = index_video(store, backend, path, progress, args.force)
                    outcomes.append(result)
                    print(f'  {result["status"]}; {result.get("selected_frames", 0)} scene frames',
                          file=sys.stderr)
                except Exception as exc:
                    errors.append({'path': str(path), 'error': f'{type(exc).__name__}: {exc}'})
                    print(f'  failed: {errors[-1]["error"]}', file=sys.stderr)
            print_json({'indexed': outcomes, 'errors': errors, 'index_path': str(store.path),
                        'index_disk_bytes': store.disk_bytes()})
            return 2 if errors else 0

        if args.command == 'search':
            backend = backend_factory(args.backend)
            results, timing = search(store, backend, args.text, args.limit)
            if args.json:
                print_json({'query': args.text, 'results': results, 'timing': timing,
                            'npu_verified': False})
            else:
                for rank, item in enumerate(results, 1):
                    print(f'{rank}. id={item["result_id"]}  {item["filename"]}  '
                          f'{item["timestamp_s"]:.3f}s  score={item["similarity"]:.5f}')
                    print(f'   thumbnail: {item["thumbnail"]}')
                print(f'Query: {timing["query_ms"]:.1f} ms; {timing["indexed_frames"]} indexed frames')
            if args.open is not None:
                if not 1 <= args.open <= len(results):
                    raise ValueError('--open rank is outside the returned results')
                opened = open_result(store, results[args.open - 1]['result_id'], args.player)
                print(f'Opened {opened["filename"]} at {opened["timestamp_s"]:.3f}s'
                      + (f'; browser URL: {opened["url"]}' if 'url' in opened else ''))
            return 0

        if args.command == 'open':
            print_json(open_result(store, args.result_id, args.player))
            return 0

        videos = store.videos()
        if args.command == 'status':
            print_json({'index_path': str(store.path), 'videos': videos,
                        'selected_frames': sum(v['selected_frames'] for v in videos),
                        'index_disk_bytes': store.disk_bytes()})
            return 0
        if args.command == 'metrics':
            print_json({'index_path': str(store.path), 'videos': videos,
                        'index_disk_bytes': store.disk_bytes(),
                        'measurement_note': 'Index durations are per-video local runs; logical storage excludes SQLite page overhead. Query latency is printed by search for a prebuilt index.'})
            return 0
    raise AssertionError('Unreachable command')


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, FileNotFoundError, KeyError, RuntimeError) as exc:
        print(f'ClipTrail: {exc}', file=sys.stderr)
        raise SystemExit(2) from exc
