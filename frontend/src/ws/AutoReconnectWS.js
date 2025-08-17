// src/ws/AutoReconnectWS.js
// 自動再接続WSラッパ
export default class AutoReconnectWS {
  constructor(url, { onOpen, onClose, onMessage, onError } = {}) {
    this.url = url;
    this.handlers = { onOpen, onClose, onMessage, onError };
    this.ws = null;
    this._retry = 0;
    this._manualClose = false;
    this._connect();
  }

  _connect() {
    this.ws = new WebSocket(this.url);
    this.ws.binaryType = "arraybuffer";

    this.ws.onopen = (e) => {
      this._retry = 0;
      this.handlers.onOpen && this.handlers.onOpen(e);
    };

    this.ws.onmessage = (e) => {
      this.handlers.onMessage && this.handlers.onMessage(e);
    };

    this.ws.onclose = (e) => {
      this.handlers.onClose && this.handlers.onClose(e);
      if (!this._manualClose) {
        const delay = Math.min(1000 * 2 ** this._retry, 15000);
        this._retry++;
        setTimeout(() => this._connect(), delay);
      }
    };

    this.ws.onerror = (e) => {
      this.handlers.onError && this.handlers.onError(e);
    };
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(data);
      return true;
    }
    return false;
  }

  close() {
    this._manualClose = true;
    if (this.ws) this.ws.close();
  }

  get ready() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }
}
