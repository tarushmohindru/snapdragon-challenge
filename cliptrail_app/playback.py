"""Launch a local video player at a search result's playback timestamp."""
from pathlib import Path
import html
import shutil
import subprocess
import webbrowser


def player_command(path, timestamp_s, player=None):
    video = Path(path).resolve()
    if not video.is_file():
        raise FileNotFoundError(f'Indexed video is missing: {video}')
    if timestamp_s < 0:
        raise ValueError('Playback timestamp must be nonnegative')
    if player is None:
        player = next((name for name in ('mpv', 'ffplay', 'vlc') if shutil.which(name)), 'browser')
    executable = shutil.which(player) or str(Path(player).resolve())
    if not Path(executable).is_file():
        raise FileNotFoundError(f'Player executable not found: {player}')
    name = Path(executable).stem.casefold()
    moment = f'{timestamp_s:.3f}'
    if name == 'mpv':
        return [executable, f'--start={moment}', str(video)]
    if name == 'ffplay':
        return [executable, '-ss', moment, '-i', str(video)]
    if name == 'vlc':
        return [executable, f'--start-time={moment}', str(video)]
    raise ValueError('Player must be mpv, ffplay or vlc (including an explicit executable path)')


def playback_source(store, result_id):
    """Resolve a stored result to its original local media and timestamp."""
    result = store.result(result_id)
    if result is None:
        raise KeyError(f'Result ID {result_id} is not in this index')
    video = Path(result['path']).resolve()
    if not video.is_file():
        raise FileNotFoundError(f'Indexed video is missing: {video}')
    return result, video


def open_result(store, result_id, player=None):
    result, video = playback_source(store, result_id)
    if player == 'browser' or (player is None and not any(
            shutil.which(name) for name in ('mpv', 'ffplay', 'vlc'))):
        viewer = store.path.parent / 'viewers' / f'{result_id}.html'
        viewer.parent.mkdir(parents=True, exist_ok=True)
        title = html.escape(video.name)
        src = html.escape(video.as_uri(), quote=True)
        at = float(result['timestamp_s'])
        page = f'''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ClipTrail — {title}</title>
<style>body{{font:16px system-ui;margin:2rem auto;max-width:960px;background:#15191f;color:#fff}}
video{{width:100%;max-height:78vh;background:#000}}</style>
<h1>{title}</h1><p>Starting at {at:.3f} seconds. Playback stays on this computer.</p>
<video controls autoplay preload="metadata" src="{src}"></video>
<script>const video=document.querySelector('video');
video.addEventListener('loadedmetadata',()=>{{video.currentTime={at:.6f};video.play().catch(()=>{{}})}},{{once:true}});</script>
</html>'''
        temp = viewer.with_suffix('.html.tmp')
        temp.write_text(page)
        temp.replace(viewer)
        url = viewer.as_uri()
        launched = webbrowser.open(url)
        return {'result_id': result_id, 'filename': result['filename'],
                'timestamp_s': result['timestamp_s'], 'viewer': str(viewer),
                'url': url, 'browser_launched': bool(launched)}
    command = player_command(result['path'], result['timestamp_s'], player)
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               start_new_session=True)
    return {'result_id': result_id, 'filename': result['filename'],
            'timestamp_s': result['timestamp_s'], 'player_pid': process.pid,
            'command': command}
