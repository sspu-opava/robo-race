import RobotWindow from './wwi_client.js?v=offline-1';

const $ = selector => document.querySelector(selector);
const source = $('#source');
const lineNumbers = $('#lineNumbers');
const codeHighlight = $('#codeHighlight');
const diagnostic = $('#diagnostic');
const helpDialog = $('#helpDialog');
const examples = {
  starter: 'PLYN(35)\nDOPREDU(1.5)\nBRZDA(0.6)\n',
  turn: 'PLYN(40)\nDOPREDU(1.0)\nVLEVO(50, 0.8)\nDOPREDU(1.0)\nBRZDA(0.5)\n',
  sample: '# Základní trať se dvěma zatáčkami.\nPLYN(45)\nDOPREDU(5.00)\nDOPREDU(1.50)\nPLYN(35)\nVLEVO(100, 2.60)\nDOPREDU(3.80)\nVPRAVO(100, 2.60)\nPLYN(45)\nDOPREDU(5.00)\nDOPREDU(1.50)\nBRZDA(0.60)\n'
};
let robotWindow;
let latestLine = null;
let currentCheckpoint = 0;
let busy = false;
let connected = false;
let requestCounter = 0;
let officialRunsPerPlayer = 2;

function requestId() { return `rr-${Date.now()}-${++requestCounter}`; }
function send(payload) {
  if (!robotWindow || !connected) return showDiagnostic('Spusť simulaci tlačítkem Run ve Webots a počkej na připojení.', 'error');
  if (!robotWindow.send(JSON.stringify({...payload, request_id: payload.request_id || requestId()})))
    showDiagnostic('Spojení s Webots bylo přerušeno. Obnovuji připojení…', 'error');
}
function showDiagnostic(message, kind = '') {
  diagnostic.className = `diagnostic ${kind}`.trim();
  diagnostic.lastElementChild.textContent = message;
}
function renderEditor() {
  const rows = source.value.split('\n');
  lineNumbers.replaceChildren();
  codeHighlight.replaceChildren();
  rows.forEach((row, index) => {
    const gutterRow = document.createElement('span');
    gutterRow.textContent = String(index + 1);
    if (latestLine === index + 1) gutterRow.className = 'active';
    lineNumbers.append(gutterRow);
    const codeRow = document.createElement('span');
    if (latestLine === index + 1) codeRow.classList.add('active');
    const commentStart = row.indexOf('#');
    if (commentStart >= 0) {
      codeRow.append(document.createTextNode(row.slice(0, commentStart)));
      const comment = document.createElement('span');
      comment.className = 'comment';
      comment.textContent = row.slice(commentStart);
      codeRow.append(comment);
    } else codeRow.textContent = row;
    codeHighlight.append(codeRow, document.createTextNode('\n'));
  });
  $('#instructionCount').textContent = `${rows.filter(row => row.trim() && !row.trim().startsWith('#')).length} / 40`;
  syncScroll();
}
function syncScroll() {
  codeHighlight.scrollTop = source.scrollTop;
  codeHighlight.scrollLeft = source.scrollLeft;
  lineNumbers.scrollTop = source.scrollTop;
}
function setBusy(value) {
  busy = value;
  for (const button of [$('#validate'), $('#test'), $('#official'), $('#newCompetitor')]) button.disabled = value || !connected;
  $('#courseLevel').disabled = value || !connected;
  for (const button of [$('#reset'), $('#restoreView'), $('#adminReset')]) button.disabled = !connected;
  $('#nickname').disabled = value;
  source.readOnly = value;
}
function formatTime(value) { return value !== null && value !== undefined && Number.isFinite(Number(value)) ? `${Number(value).toFixed(2)} s` : '—'; }
function renderLeaderboard(rows = []) {
  const target = $('#leaderboard');
  target.replaceChildren();
  if (!rows.length) {
    const empty = document.createElement('li');
    empty.className = 'empty-row';
    empty.textContent = 'Zatím tu nikdo není. První místo čeká na tebe.';
    target.append(empty);
    $('#bestTime').textContent = '—';
    return;
  }
  rows.slice(0, 10).forEach((row, index) => {
    const item = document.createElement('li');
    const rank = document.createElement('span'); rank.className = `rank ${index === 0 ? 'first' : ''}`; rank.textContent = String(index + 1).padStart(2, '0');
    const name = document.createElement('span'); name.className = 'player-name'; name.textContent = row.nickname;
    const time = document.createElement('span'); time.className = 'player-time'; time.textContent = formatTime(row.final_time);
    item.append(rank, name, time); target.append(item);
  });
  $('#bestTime').textContent = formatTime(rows[0].final_time);
}
function renderCheckpoints(completed) {
  const items = [...document.querySelectorAll('.checkpoint')];
  items.forEach((item, index) => {
    item.classList.toggle('passed', index < completed);
    item.classList.toggle('active', index === completed);
  });
}
function showResult(result) {
  setBusy(false);
  const card = $('#resultCard');
  const success = Boolean(result.valid);
  card.hidden = false;
  card.classList.toggle('failed', !success);
  $('#resultIcon').textContent = success ? '✓' : '!';
  $('#resultEyebrow').textContent = result.mode === 'official' ? 'SOUTĚŽNÍ VÝSLEDEK' : 'VÝSLEDEK TESTU';
  $('#resultHeading').textContent = success ? 'Cíl projet!' : 'Neplatný pokus';
  $('#resultMessage').textContent = result.reason || '';
  if (Array.isArray(result.position)) $('#position').textContent = `${result.position[0].toFixed(2)}, ${result.position[1].toFixed(2)} m`;
  $('#activeLine').textContent = result.source_line ? `Řádek ${result.source_line}` : '—';
  $('#resultRaw').textContent = formatTime(result.raw_time);
  $('#resultFinal').textContent = success ? formatTime(result.final_time) : 'DNF';
  $('#raceState').textContent = success ? 'Dokončeno' : 'Nedokončeno';
  $('#livePill').textContent = success ? 'CÍL' : 'DNF';
  $('#livePill').className = `live-pill ${success ? 'done' : 'failed'}`;
  $('#elapsed').innerHTML = `${Number(result.raw_time).toFixed(2)} <small>s</small>`;
  $('#penalties').innerHTML = `${result.penalties} <small>/ +${Number(result.penalty_seconds).toFixed(2)} s</small>`;
  $('#checkpoints').innerHTML = `${result.checkpoint || 0} <small>/ ${result.checkpoint_total || 3}</small>`;
  renderCheckpoints(result.checkpoint || 0);
  if (result.leaderboard) renderLeaderboard(result.leaderboard);
  showDiagnostic(success ? `Výsledný čas ${formatTime(result.final_time)}. Můžeš upravit program a zkusit to znovu.` : result.reason, success ? 'success' : 'error');
}

function onMessage(raw) {
  let message;
  try { message = JSON.parse(raw); } catch (_) { return; }
  if (message.type === 'ready') {
    connected = true;
    setBusy(['COUNTDOWN', 'RUNNING'].includes(message.state));
    if (message.state === 'IDLE') $('#raceState').textContent = 'Připraven';
    $('#connection').classList.add('connected');
    $('#connection').lastElementChild.textContent = `Připojeno · krok ${message.basic_time_step_ms} ms`;
    $('#configId').textContent = `Konfigurace tratě: ${message.config_id || '—'}`;
    officialRunsPerPlayer = message.official_runs_per_player || 2;
    $('#attemptNote').textContent = `Oficiální pokusy v této relaci: ${officialRunsPerPlayer}`;
    if (message.sample_program) examples.sample = message.sample_program;
    $('#courseLevel').value = String(message.level || 1);
    const selectedLevel = (message.levels || []).find(level => level.id === (message.level || 1));
    $('#levelDescription').textContent = selectedLevel?.description || '';
    renderLeaderboard(message.leaderboard || []);
    if (message.warning) showDiagnostic(message.warning, 'warning');
    else showDiagnostic('Webots je připraven. Ověř program nebo spusť první test.', 'success');
  } else if (message.type === 'validation_result') {
    if (message.valid) {
      const warningText = (message.warnings || []).join(' ');
      showDiagnostic(`Program je v pořádku: ${message.instruction_count} příkazů.${warningText ? ` ${warningText}` : ''}`, warningText ? 'warning' : 'success');
    } else {
      showDiagnostic(`Řádek ${message.line}: ${message.message}`, 'error');
      latestLine = message.line; renderEditor();
    }
  } else if (message.type === 'accepted') {
    $('#resultCard').hidden = true;
    setBusy(true);
    $('#raceState').textContent = 'Připravuji start';
    $('#livePill').textContent = 'START ZA CHVÍLI'; $('#livePill').className = 'live-pill running';
    $('#elapsed').innerHTML = '00.00 <small>s</small>';
    $('#penalties').innerHTML = '0 <small>/ +0.00 s</small>';
    if (message.mode === 'official' && Number.isFinite(message.remaining_attempts)) $('#attemptNote').textContent = `Oficiální pokusy zbývají: ${message.remaining_attempts}`;
    latestLine = null; currentCheckpoint = 0; renderEditor(); renderCheckpoints(0);
    showDiagnostic(message.mode === 'official' ? `Oficiální pokus ${message.nickname}.` : 'Testovací jízda spuštěna.', 'success');
  } else if (message.type === 'execution') {
    if (message.state === 'COUNTDOWN' || message.state === 'RUNNING') setBusy(true);
    if (message.state === 'RUNNING') {
      $('#raceState').textContent = 'Robot jede';
      $('#livePill').textContent = 'LIVE'; $('#livePill').className = 'live-pill running';
    } else if (message.state === 'COUNTDOWN') $('#raceState').textContent = 'Odpočet';
    $('#elapsed').innerHTML = `${Number(message.elapsed || 0).toFixed(2)} <small>s</small>`;
    $('#penalties').innerHTML = `${message.penalties || 0} <small>/ +${Number(message.penalty_seconds || 0).toFixed(2)} s</small>`;
    $('#checkpoints').innerHTML = `${message.checkpoint || 0} <small>/ ${message.checkpoint_total || 3}</small>`;
    currentCheckpoint = Number(message.checkpoint || 0);
    renderCheckpoints(currentCheckpoint);
    if (message.source_line) { latestLine = message.source_line; renderEditor(); $('#activeLine').textContent = `Řádek ${message.source_line}`; }
    else $('#activeLine').textContent = '—';
    if (Array.isArray(message.position)) $('#position').textContent = `${message.position[0].toFixed(2)}, ${message.position[1].toFixed(2)} m`;
  } else if (message.type === 'result') showResult(message);
  else if (message.type === 'level_changed') {
    examples.sample = message.sample_program;
    source.value = message.sample_program;
    latestLine = null;
    renderEditor(); renderCheckpoints(0);
    $('#courseLevel').value = String(message.level);
    $('#levelDescription').textContent = message.description;
    $('#configId').textContent = `Konfigurace tratě: ${message.config_id}`;
    $('#attemptNote').textContent = `Oficiální pokusy v této relaci: ${officialRunsPerPlayer}`;
    $('#raceState').textContent = 'Připraven';
    $('#livePill').textContent = 'ČEKÁ'; $('#livePill').className = 'live-pill';
    $('#elapsed').innerHTML = '00.00 <small>s</small>';
    $('#checkpoints').innerHTML = '0 <small>/ 3</small>';
    $('#penalties').innerHTML = '0 <small>/ +0.00 s</small>';
    $('#activeLine').textContent = '—'; $('#position').textContent = '—';
    $('#resultCard').hidden = true;
    renderLeaderboard(message.leaderboard || []);
    if (message.warning) showDiagnostic(message.warning, 'warning');
    else showDiagnostic(`Načtena trasa: ${message.name}.`, 'success');
  }
  else if (message.type === 'view_restored') showDiagnostic(message.message, 'success');
  else if (message.type === 'error') {
    if (message.line) { latestLine = message.line; renderEditor(); }
    showDiagnostic(message.line ? `Řádek ${message.line}: ${message.message}` : message.message, 'error');
  } else if (message.type === 'reset') {
    setBusy(false); latestLine = null; renderEditor(); renderCheckpoints(0);
    $('#raceState').textContent = 'Připraven'; $('#livePill').textContent = 'ČEKÁ'; $('#livePill').className = 'live-pill';
    $('#elapsed').innerHTML = '00.00 <small>s</small>'; $('#penalties').innerHTML = '0 <small>/ +0.00 s</small>';
    $('#checkpoints').innerHTML = '0 <small>/ 3</small>'; $('#activeLine').textContent = '—'; $('#position').textContent = '—';
    $('#resultCard').hidden = true; showDiagnostic('Robot je zpět na startu.', 'success');
  } else if (message.type === 'leaderboard') {
    renderLeaderboard(message.entries || []); if (message.message) showDiagnostic(message.message, 'success');
  } else if (message.type === 'competitor_ready') {
    $('#nickname').value = message.nickname;
    $('#attemptNote').textContent = `Oficiální pokusy zbývají: ${message.remaining_attempts}`;
    showDiagnostic(`${message.nickname}: ${message.message}`, 'success');
  }
}

$('#validate').addEventListener('click', () => send({type: 'validate', source: source.value}));
$('#test').addEventListener('click', () => send({type: 'start', mode: 'test', source: source.value}));
$('#official').addEventListener('click', () => send({type: 'start', mode: 'official', nickname: $('#nickname').value, source: source.value}));
$('#reset').addEventListener('click', () => send({type: 'reset'}));
$('#restoreView').addEventListener('click', () => send({type: 'restore_view'}));
$('#courseLevel').addEventListener('change', event => send({type: 'set_level', level: Number(event.target.value)}));
$('#newCompetitor').addEventListener('click', () => send({type: 'new_competitor', nickname: $('#nickname').value}));
$('#adminReset').addEventListener('click', () => {
  if (window.confirm('Opravdu vymazat místní žebříček této konfigurace tratě?')) send({type: 'admin_reset', confirm: true});
});
for (const trigger of [$('#helpButton'), $('#editorHelp')]) {
  trigger.addEventListener('click', () => helpDialog.showModal());
}
$('#closeHelp').addEventListener('click', () => helpDialog.close());
helpDialog.addEventListener('click', event => {
  if (event.target === helpDialog) helpDialog.close();
});
document.querySelectorAll('[data-example]').forEach(button => button.addEventListener('click', () => {
  if (busy) return;
  source.value = examples[button.dataset.example]; latestLine = null; renderEditor(); showDiagnostic('Příklad načten. Stiskni „Ověřit“ nebo rovnou „Testovat“.', 'success');
}));
source.addEventListener('input', renderEditor);
source.addEventListener('scroll', syncScroll);
source.addEventListener('click', () => { if (!busy) latestLine = null; renderEditor(); });
source.addEventListener('keyup', () => { if (!busy) { latestLine = null; renderEditor(); } });
window.addEventListener('resize', syncScroll);

source.value = examples.starter; renderEditor(); setBusy(false);
try {
  robotWindow = new RobotWindow();
  robotWindow.receive = onMessage;
  robotWindow.connectionChanged = isConnected => {
    if (isConnected) return;
    connected = false;
    setBusy(busy);
    $('#connection').classList.remove('connected');
    $('#connection').lastElementChild.textContent = 'Obnovuji připojení…';
    showDiagnostic('Spusť simulaci tlačítkem Run ve Webots. Panel se připojí automaticky.', 'warning');
  };
} catch (error) {
  $('#connection').lastElementChild.textContent = 'Webots není připojen';
  showDiagnostic(error.message, 'error');
}
