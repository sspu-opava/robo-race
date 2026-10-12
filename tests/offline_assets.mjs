// Offline regression check: reads local files and uses a fake WebSocket.
// No server, internet connection, browser package or npm install is needed.
import assert from 'node:assert/strict';
import {readFile, readdir, access} from 'node:fs/promises';

const root = new URL('../', import.meta.url);
async function checkLocalReference(reference, owner) {
  assert(!/^(?:[a-z]+:|\/\/)/i.test(reference), `External asset in ${owner}: ${reference}`);
  const target = new URL(reference, new URL(owner, root));
  await access(target);
}

const panel = 'plugins/robot_windows/roborace/';
const html = await readFile(new URL(panel + 'roborace.html', root), 'utf8');
for (const match of html.matchAll(/(?:src|href)="([^"]+)"/g))
  await checkLocalReference(match[1], panel + 'roborace.html');
assert.match(html, /default-src 'none'/);
assert.match(html, /script-src 'self'/);
assert.match(html, /style-src 'self'/);
const connections = html.match(/connect-src ([^;"]+)/)?.[1].split(/\s+/);
assert(connections?.length);
for (const endpoint of connections)
  assert.match(endpoint, /^wss?:\/\/(localhost|127\.0\.0\.1|\[::1\]):\*$/);

for (const name of ['roborace.js', 'wwi_client.js']) {
  const code = await readFile(new URL(panel + name, root), 'utf8');
  assert.doesNotMatch(code, /\b(?:fetch|XMLHttpRequest|EventSource|sendBeacon)\s*\(/);
  for (const match of code.matchAll(/\bimport\s+.*?from\s+['"]([^'"]+)['"]/g))
    await checkLocalReference(match[1], panel + name);
}
const css = await readFile(new URL(panel + 'style.css', root), 'utf8');
assert.doesNotMatch(css, /@import|url\s*\(/i);
for (const path of ['worlds/roborace.wbt', 'protos/RoboRaceCar.proto',
                    'protos/CourseRoad.proto', 'protos/CourseGate.proto']) {
  const text = await readFile(new URL(path, root), 'utf8');
  assert.doesNotMatch(text, /https?:\/\//i);
  for (const match of text.matchAll(/EXTERNPROTO\s+"([^"]+)"/g))
    await checkLocalReference(match[1], path);
}

const sockets = [];
class LocalSocket extends EventTarget {
  static OPEN = 1;
  readyState = LocalSocket.OPEN;
  sent = [];
  constructor(url) { super(); this.url = url; sockets.push(this); }
  send(text) { this.sent.push(text); }
  close() { this.readyState = 3; }
}
globalThis.WebSocket = LocalSocket;
const clientSource = await readFile(new URL(panel + 'wwi_client.js', root), 'utf8');
const {default: RobotWindow} = await import(
  `data:text/javascript;base64,${Buffer.from(clientSource).toString('base64')}`
);
function setPage(url) {
  globalThis.window = new EventTarget();
  window.location = {href: url};
}
for (const [origin, endpoint] of [
  ['http://localhost:1234', 'ws://localhost:1234/'],
  ['http://127.0.0.1:1234', 'ws://127.0.0.1:1234/'],
  ['http://[::1]:1234', 'ws://[::1]:1234/'],
  ['https://localhost:1234', 'wss://localhost:1234/'],
]) {
  setPage(origin + '/robot_windows/roborace/roborace.html?name=RoboRace%20car');
  const client = new RobotWindow();
  assert.equal(client.wsServer, endpoint);
  client.socket.dispatchEvent(new Event('open'));
  assert.deepEqual(client.socket.sent, [
    'robot:RoboRace car:init robot window',
    'robot:RoboRace car:{"type":"hello"}'
  ]);
  window.dispatchEvent(new Event('beforeunload'));
}
for (const url of [
  'https://example.com/robot_windows/roborace/roborace.html',
  'http://localhost.example.com/robot_windows/roborace/roborace.html',
  'http://127.0.0.1.example.com/robot_windows/roborace/roborace.html',
  'http://user:password@localhost:1234/robot_windows/roborace/roborace.html',
  'file:///E:/astra/robo-race/plugins/robot_windows/roborace/roborace.html',
  'http://localhost:1234/other.html?path=/robot_windows/',
]) {
  setPage(url);
  const before = sockets.length;
  assert.throws(() => new RobotWindow());
  assert.equal(sockets.length, before, 'Rejected origin must not open a socket');
}

// All tutorial stages must remain readable and navigable from local files.
const tutorial = 'docs/vyukovy-postup/';
for (const name of await readdir(new URL(tutorial, root))) {
  if (!name.endsWith('.md')) continue;
  const markdown = await readFile(new URL(tutorial + name, root), 'utf8');
  assert.equal([...markdown.matchAll(/^```/gm)].length % 2, 0, name);
  for (const match of markdown.matchAll(/\]\(([^)]+)\)/g)) {
    if (/^https?:/i.test(match[1])) continue;
    await checkLocalReference(match[1].split('#')[0], tutorial + name);
  }
}
console.log('Offline: local assets, loopback-only WWI, handshake, rejected remote origins and tutorial links OK');
