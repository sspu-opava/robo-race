// Local Webots Robot Window WebSocket client, compatible with the documented WWI.
// It speaks to the Webots process serving this project; it does not contact a cloud service.
export default class RobotWindow {
  constructor() {
    const pageUrl = new URL(window.location.href);
    if (!['http:', 'https:'].includes(pageUrl.protocol) ||
        !['localhost', '127.0.0.1', '[::1]'].includes(pageUrl.hostname) ||
        pageUrl.username || pageUrl.password)
      throw new Error('Panel musí být otevřen přes místní Webots (localhost).');
    this.name = pageUrl.searchParams.get('name') || 'undefined';
    if (!pageUrl.pathname.includes('/~WEBOTS_HOME/') &&
        !pageUrl.pathname.includes('/robot_windows/'))
      throw new Error('Robot Window nebyl otevřen přes Webots.');
    // Only loopback origins are permitted; no DNS or external server is needed.
    this.wsServer = pageUrl.origin.replace(/^http/, 'ws') + '/';
    this.closed = false;
    this.reconnectTimer = null;
    this.connect();
    window.addEventListener('beforeunload', () => {
      this.closed = true;
      clearTimeout(this.reconnectTimer);
      this.socket.close();
    });
  }

  connect() {
    this.socket = new WebSocket(this.wsServer);
    this.socket.addEventListener('open', () => {
      this.connectionChanged(true);
      this.send('init robot window');
      // Webots handles the init message itself. An application handshake is
      // required to request fresh state when opening the panel after startup.
      this.send(JSON.stringify({type: 'hello'}));
    });
    this.socket.addEventListener('message', event => this._receive(event.data));
    this.socket.addEventListener('error', () => this.connectionChanged(false));
    this.socket.addEventListener('close', () => {
      this.connectionChanged(false);
      if (!this.closed) this.reconnectTimer = setTimeout(() => this.connect(), 1000);
    });
  }

  send(message) {
    const payload = String(message);
    if (this.socket.readyState !== WebSocket.OPEN) return false;
    this.socket.send(`robot:${this.name}:${payload}`);
    return true;
  }

  receive(_message, _robot) {}
  connectionChanged(_connected) {}

  _receive(data) {
    for (const line of String(data).split(/\r?\n/)) {
      if (!line.startsWith('robot:')) continue;
      const start = line.indexOf('{');
      if (start < 0) continue;
      try {
        const envelope = JSON.parse(line.slice(start));
        if (envelope.name === this.name) this.receive(envelope.message, envelope.name);
      } catch (_) {
        // Other Webots message formats are ignored; malformed telemetry is not executable.
      }
    }
  }
}
