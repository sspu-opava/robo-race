// Optional end-to-end smoke runner. Start Webots with this project first.
const port = Number(process.argv[2] || 1234);
const timeoutMs = Number(process.argv[3] || 45000);
const robotName = "RoboRace car";
const socket = new WebSocket(`ws://127.0.0.1:${port}`);
let started = false;
let finished = false;

const timeout = setTimeout(() => {
  if (!finished) {
    console.error("Timeout: Webots nevrátil výsledek ukázkové jízdy.");
    process.exit(4);
  }
}, timeoutMs);

socket.addEventListener("open", () => {
  console.log(`Připojeno k WWI na portu ${port}.`);
  socket.send(`robot:${robotName}:init robot window`);
  socket.send(`robot:${robotName}:${JSON.stringify({type: 'hello'})}`);
});
socket.addEventListener("message", event => {
  for (const line of String(event.data).split(/\r?\n/)) {
    if (!line.startsWith("robot:")) continue;
    const start = line.indexOf("{");
    if (start < 0) continue;
    try {
      const envelope = JSON.parse(line.slice(start));
      if (envelope.name !== robotName) continue;
      const message = JSON.parse(envelope.message);
      if (["ready", "accepted", "error", "result"].includes(message.type)) {
        console.log(`${message.type}: ${message.message || message.state || ""}`);
      }
      if (message.type === "ready" && !started) {
        started = true;
        socket.send(`robot:${robotName}:${JSON.stringify({
          type: "start",
          request_id: `smoke-${Date.now()}`,
          mode: "test",
          source: message.sample_program
        })}`);
      }
      if (message.type === "result") {
        finished = true;
        clearTimeout(timeout);
        console.log(JSON.stringify(message));
        socket.close();
        process.exitCode = message.valid ? 0 : 1;
        setTimeout(() => process.exit(message.valid ? 0 : 1), 40);
      }
    } catch (_) {
      // Ignore unrelated Webots messages and malformed telemetry.
    }
  }
});
socket.addEventListener("error", () => {
  clearTimeout(timeout);
  console.error(`Nepodařilo se připojit k Robot Window na portu ${port}.`);
  process.exit(3);
});
