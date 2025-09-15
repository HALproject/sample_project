// src/components/ControlPanel.jsx
import React, { useState, useRef, useEffect } from "react";
import AudioRecorder from "../utils/AudioRecorder";

export default function ControlPanel({ onResult }) {
  const [recording, setRecording] = useState(false);
  const wsRef = useRef(null);
  const recorderRef = useRef(null);

  useEffect(() => {
    wsRef.current = new WebSocket("ws://localhost:8000/ws");
    wsRef.current.binaryType = "arraybuffer";

    wsRef.current.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      // partial: true → リアルタイム部分テキスト(status:partial)
      onResult(msg);
    };

    wsRef.current.onclose = () => console.log("WebSocket closed");
    wsRef.current.onerror = (err) => console.error("WebSocket error", err);

    return () => {
      wsRef.current.close();
    };
  }, [onResult]);

  const startRecording = async () => {
    setRecording(true);
    recorderRef.current = new AudioRecorder((float32Data) => {
      // PCM16bit に変換して送信
      const int16Buffer = float32ToInt16(float32Data);
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(int16Buffer);
      }
    });

    try {
      await recorderRef.current.start();
      // バックエンドに /init_ws → /start_ws を呼ぶ
      await fetch("/init_ws");
      await fetch("/start_ws");
    } catch (err) {
      console.error("AudioRecorder start error:", err);
    }
  };

  const stopRecording = async () => {
    setRecording(false);
    if (recorderRef.current) {
      recorderRef.current.stop();
      recorderRef.current = null;
    }
    // バックエンドに録音終了通知
    await fetch("/stop_ws3");
    await fetch("/end_ws");
  };

  const float32ToInt16 = (float32Array) => {
    const buffer = new ArrayBuffer(float32Array.length * 2);
    const view = new DataView(buffer);
    for (let i = 0; i < float32Array.length; i++) {
      let s = Math.max(-1, Math.min(1, float32Array[i]));
      view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }
    return buffer;
  };

  return (
    <div className="mb-4">
      <button
        onClick={recording ? stopRecording : startRecording}
        className={`px-4 py-2 rounded text-white ${
          recording ? "bg-red-500" : "bg-green-500"
        }`}
      >
        {recording ? "Stop" : "Start Recording"}
      </button>
    </div>
  );
}
