const token = document.querySelector('meta[name="cliptrail-token"]').content;
const $ = id => document.getElementById(id);
const supported = /\.(mp4|mov|mkv|m4v|avi|webm)$/i;
let activeResult = null;
let lastPhase = 'starting';
let uploading = false;
let searching = false;

async function api(path, options = {}) {
  const headers = {'X-ClipTrail-Token': token, ...(options.headers || {})};
  const response = await fetch(path, {...options, headers});
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || `Request failed: ${response.status}`);
  return body;
}

function note(text, isError = false) {
  $('activityText').textContent = text;
  $('activity').classList.toggle('error', isError);
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  return `${mins}:${(seconds % 60).toFixed(1).padStart(4, '0')}`;
}

function renderVideos(videos) {
  $('count').textContent = `${videos.length} video${videos.length === 1 ? '' : 's'}`;
  const container = $('videos');
  container.replaceChildren();
  if (!videos.length) {
    const empty = document.createElement('div'); empty.className = 'empty';
    empty.textContent = 'No videos indexed yet.'; container.append(empty); return;
  }
  for (const video of videos) {
    const row = document.createElement('div'); row.className = 'video-item';
    const detail = document.createElement('div');
    const title = document.createElement('strong'); title.textContent = video.filename;
    const more = document.createElement('small');
    more.textContent = `${formatTime(video.duration_s)} · ${video.path}`;
    detail.append(title, more);
    const frames = document.createElement('span'); frames.className = 'count';
    frames.textContent = `${video.selected_frames} scenes`;
    row.append(detail, frames); container.append(row);
  }
}

function renderStatus(data) {
  const state = data.state;
  lastPhase = state.phase;
  const displayPhase = searching ? 'searching' : state.phase;
  $('backend').textContent = data.backend_label;
  $('verification').textContent = data.backend === 'cpu'
    ? 'CPU CLIP backend' : 'Experimental QNN backend · hardware execution unverified';
  const pill = $('phase'); pill.textContent = displayPhase;
  pill.className = `pill ${displayPhase === 'ready' ? '' : 'busy'}`;
  if (!uploading) note(searching ? 'Searching local index…' : state.message);
  $('activityDetail').textContent = state.phase === 'indexing'
    ? `${state.completed}/${state.total} videos · ${state.current || ''} · ${state.stage || ''}`
    : state.errors.length ? state.errors.map(e => `${e.filename}: ${e.error}`).join(' · ')
    : `${data.index_disk_bytes.toLocaleString()} bytes in local index`;
  const progress = $('progress');
  progress.max = Math.max(state.total, 1);
  progress.value = state.completed;
  if (state.phase === 'indexing' && state.progress_total) {
    progress.max = state.total;
    progress.value = state.completed + Math.min(1, state.progress_count / state.progress_total);
  }
  const busy = displayPhase !== 'ready' || uploading;
  for (const id of ['chooseVideo', 'chooseFolder', 'searchButton']) $(id).disabled = busy;
  renderVideos(data.videos);
}

async function poll() {
  try { renderStatus(await api('/api/status')); }
  catch (error) { $('phase').className = 'pill error'; $('phase').textContent = 'error'; note(error.message, true); }
}

async function startIndex(paths) {
  await api('/api/index', {method: 'POST', headers: {'Content-Type':'application/json'},
                          body: JSON.stringify({paths})});
  note('Indexing started'); await poll();
}

function upload(file, name) {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    const safePath = name.split('/').map(encodeURIComponent).join('/');
    request.open('PUT', `/api/upload/${safePath}`);
    request.setRequestHeader('X-ClipTrail-Token', token);
    request.upload.onprogress = event => {
      if (event.lengthComputable) note(`Copying ${file.name}: ${Math.round(event.loaded / event.total * 100)}%`);
    };
    request.onload = () => {
      let result;
      try { result = JSON.parse(request.responseText); } catch { reject(new Error('Upload response was invalid')); return; }
      if (request.status !== 200) reject(new Error(result.error || 'Upload failed'));
      else resolve(result.path);
    };
    request.onerror = () => reject(new Error('Local upload failed'));
    request.send(file);
  });
}

async function uploadSelection(input) {
  const files = [...input.files].filter(file => supported.test(file.name));
  if (!files.length) { note('Choose a supported video file.', true); return; }
  uploading = true; await poll();
  try {
    const paths = [];
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      note(`Copying ${i + 1}/${files.length}: ${file.name}`);
      paths.push(await upload(file, file.webkitRelativePath || file.name));
    }
    uploading = false;
    await startIndex(paths);
  } catch (error) { uploading = false; note(error.message, true); }
  finally { input.value = ''; await poll(); }
}

function renderResults(results) {
  const container = $('results'); container.replaceChildren();
  if (!results.length) {
    const empty = document.createElement('div'); empty.className = 'empty';
    empty.textContent = 'No results. Index a video first, then search again.';
    container.append(empty); return;
  }
  for (const result of results) {
    const button = document.createElement('button'); button.className = 'result';
    button.type = 'button'; button.setAttribute('aria-label',
      `Play ${result.filename} at ${formatTime(result.timestamp_s)}`);
    const image = document.createElement('img'); image.src = result.thumbnail_url;
    image.alt = `Scene from ${result.filename}`;
    const detail = document.createElement('div');
    const name = document.createElement('div'); name.className = 'name'; name.textContent = result.filename;
    const meta = document.createElement('div'); meta.className = 'meta';
    meta.textContent = `Play at ${formatTime(result.timestamp_s)}`;
    detail.append(name, meta);
    const score = document.createElement('span'); score.className = 'score';
    score.textContent = `score ${result.similarity.toFixed(3)}`;
    button.append(image, detail, score);
    button.addEventListener('click', () => playResult(result));
    container.append(button);
  }
}

function playResult(result) {
  activeResult = result;
  $('playerName').textContent = result.filename;
  $('playerTime').textContent = `Starting at ${formatTime(result.timestamp_s)}`;
  $('playbackMessage').textContent = 'Loading local video…';
  const player = $('player');
  player.src = `/api/video/${result.result_id}?token=${encodeURIComponent(token)}`;
  player.load();
  $('playerDialog').showModal();
}

$('player').addEventListener('loadedmetadata', () => {
  if (!activeResult) return;
  const player = $('player');
  player.currentTime = Math.min(activeResult.timestamp_s, Math.max(0, player.duration - .05));
  $('playbackMessage').textContent = `Playing from ${formatTime(player.currentTime)}.`;
  player.play().catch(() => {});
});
$('player').addEventListener('error', () => {
  $('playbackMessage').textContent = 'This browser may not support the video codec. Use a local player.';
});
$('closePlayer').addEventListener('click', () => {
  $('player').pause(); $('playerDialog').close(); activeResult = null;
});
$('openExternal').addEventListener('click', async () => {
  if (!activeResult) return;
  try {
    const opened = await api('/api/open', {method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({result_id:activeResult.result_id})});
    $('playbackMessage').textContent = opened.url
      ? `Local viewer: ${opened.url}` : 'Opened in a local player.';
  } catch (error) { $('playbackMessage').textContent = error.message; }
});

$('chooseVideo').addEventListener('click', () => $('videoFiles').click());
$('chooseFolder').addEventListener('click', () => $('folderFiles').click());
$('videoFiles').addEventListener('change', event => uploadSelection(event.target));
$('folderFiles').addEventListener('change', event => uploadSelection(event.target));
$('pathForm').addEventListener('submit', async event => {
  event.preventDefault();
  const path = $('pathInput').value.trim();
  try { await startIndex([path]); $('pathInput').value = ''; }
  catch (error) { note(error.message, true); }
});
$('searchForm').addEventListener('submit', async event => {
  event.preventDefault();
  let errorMessage = null;
  searching = true;
  $('phase').textContent = 'searching';
  $('phase').className = 'pill busy';
  $('searchButton').disabled = true;
  note('Searching local index…');
  try {
    const result = await api('/api/search', {method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({text:$('query').value,limit:8})});
    $('queryTime').textContent = `${result.timing.query_ms.toFixed(1)} ms warm query`;
    renderResults(result.results);
  } catch (error) { errorMessage = error.message; }
  finally {
    searching = false;
    await poll();
    if (errorMessage) note(errorMessage, true);
  }
});

poll(); setInterval(poll, 750);
