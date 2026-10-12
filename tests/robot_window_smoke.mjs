// Exercise the production Robot Window client against a running Webots server.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const port = Number(process.argv[2] || 1234);
globalThis.window = new EventTarget();
window.location = {href: `http://localhost:${port}/robot_windows/roborace/roborace.html?name=RoboRace%20car`};
globalThis.location = new URL(window.location.href);
const code = await readFile(new URL('../plugins/robot_windows/roborace/wwi_client.js', import.meta.url), 'utf8');
const {default: RobotWindow} = await import(`data:text/javascript;base64,${Buffer.from(code).toString('base64')}`);
const client = new RobotWindow();
const received = [];
client.receive = raw => received.push(JSON.parse(raw));

async function waitFor(predicate, start = 0, timeout = 30000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    const match = received.slice(start).find(predicate);
    if (match) return match;
    await new Promise(resolve => setTimeout(resolve, 25));
  }
  throw new Error('Webots response timed out');
}
async function request(payload, responseType) {
  const start = received.length;
  assert.equal(client.send(JSON.stringify(payload)), true);
  return waitFor(message => message.type === responseType, start);
}

try {
  const ready = await waitFor(message => message.type === 'ready');
  assert.equal(ready.level, 1);
  assert.equal(ready.levels.length, 4);
  assert.match(ready.sample_program, /PLYN\(45\)/);
  const invalid = await request({type: 'validate', source: 'PLYN(200)'}, 'validation_result');
  assert.equal(invalid.valid, false);
  assert.equal(invalid.line, 1);
  const level2 = await request({type: 'set_level', level: 2}, 'level_changed');
  assert.equal(level2.config_id, 'junior-track-v2-level-2');
  const level3 = await request({type: 'set_level', level: 3}, 'level_changed');
  assert.equal(level3.config_id, 'junior-track-v3-level-3');
  assert.match(level3.sample_program, /VLEVO\(100, 2\.60\)/);
  const level4 = await request({type: 'set_level', level: 4}, 'level_changed');
  assert.equal(level4.config_id, 'junior-track-v1-level-4');
  assert.match(level4.sample_program, /PLYN\(100\)/);
  await request({type: 'set_level', level: 1}, 'level_changed');
  await request({type: 'restore_view'}, 'view_restored');
  const start = received.length;
  await request({type: 'start', mode: 'test', source: ready.sample_program}, 'accepted');
  const result = await waitFor(message => message.type === 'result', start);
  assert.equal(result.valid, true);
  assert.equal(result.penalties, 0);
  assert.equal(result.checkpoint, 3);
  assert.equal(result.reason, 'Cíl projet.');
  // A closed connection must reopen and recover the completed result.
  const reconnectStart = received.length;
  client.socket.close();
  await waitFor(message => message.type === 'ready', reconnectStart);
  const recovered = await waitFor(message => message.type === 'result', reconnectStart);
  assert.equal(recovered.raw_time, result.raw_time);
  await request({type: 'reset'}, 'reset');
  const resetReady = await request({type: 'hello'}, 'ready');
  assert.equal(resetReady.state, 'IDLE');
  console.log(`Robot Window: four levels, validation, view, race (${result.raw_time.toFixed(3)} s), reconnect and reset OK`);
} finally {
  window.dispatchEvent(new Event('beforeunload'));
}
