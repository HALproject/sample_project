// src/audio/AudioRecorder.js
// マイク常時送信
const MIME_PREFERENCES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/ogg;codecs=opus",
  "audio/mp4" // 最終フォールバック（多くの環境で不可）
];

export default class AudioRecorder {
  constructor({ onData, chunkMs = 250 } = {}) {
    this.onData = onData;
    this.chunkMs = chunkMs;
    this.mediaStream = null;
    this.recorder = null;
    this.mimeType = null;
  }

  async start() {
    this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mimeType = MIME_PREFERENCES.find((t) => MediaRecorder.isTypeSupported(t)) || "";
    this.mimeType = mimeType;

    this.recorder = new MediaRecorder(this.mediaStream, mimeType ? { mimeType } : undefined);
    this.recorder.ondataavailable = async (e) => {
      if (!e.data || e.data.size === 0) return;
      const buf = await e.data.arrayBuffer();
      this.onData && this.onData(buf);
    };
    this.recorder.start(this.chunkMs);
  }

  stop() {
    if (this.recorder && this.recorder.state !== "inactive") {
      this.recorder.stop();
    }
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((t) => t.stop());
    }
    this.recorder = null;
    this.mediaStream = null;
  }
}
