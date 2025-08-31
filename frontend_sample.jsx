import { useState, useEffect, useRef } from "react";

export default function App() {
  const [chatLog, setChatLog] = useState([]);
  const [currentTranscript, setCurrentTranscript] = useState("");
  const wsRef = useRef(null);
  const mediaRef = useRef(null);

  useEffect(() => {
    connectWebSocket();
  }, []);

  const connectWebSocket = async () => {
    wsRef.current = new WebSocket("ws://localhost:8000/ws");

    wsRef.current.onopen = () => {
      console.log("WebSocket connected");
      startMicrophone();
    };

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "partial") {
        // 逐次更新
        setCurrentTranscript(data.text);
      }

      if (data.type === "final") {
        // finalはログに追加
        setChatLog((prev) => [
          ...prev,
          {
            text: data.text,
            sentiment: data.sentiment,
            keywords: data.keywords,
          },
        ]);
        setCurrentTranscript("");
      }
    };

    wsRef.current.onclose = () => {
      console.log("WebSocket disconnected, reconnecting...");
      setTimeout(connectWebSocket, 5000);
    };

    wsRef.current.onerror = (err) => {
      console.error("WebSocket error:", err);
    };
  };

  const startMicrophone = async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      alert("getUserMedia not supported in your browser!");
      return;
    }

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const audioContext = new (window.AudioContext || window.webkitAudioContext)({
      sampleRate: 16000,
    });
    const source = audioContext.createMediaStreamSource(stream);
    const processor = audioContext.createScriptProcessor(4096, 1, 1);

    processor.onaudioprocess = (e) => {
      const input = e.inputBuffer.getChannelData(0);
      const pcm = new Int16Array(input.length);
      for (let i = 0; i < input.length; i++) {
        pcm[i] = Math.max(-1, Math.min(1, input[i])) * 0x7fff;
      }
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(pcm.buffer);
      }
    };

    source.connect(processor);
    processor.connect(audioContext.destination);
    mediaRef.current = { stream, processor, source, audioContext };
  };

  return (
    <div style={{ padding: "2rem" }}>
      <h1>リアルタイム音声認識チャット</h1>
      <div style={{ marginBottom: "1rem" }}>
        <strong>現在の発話 (partial):</strong>
        <p>{currentTranscript}</p>
      </div>
      <div>
        <h2>チャットログ (final)</h2>
        <ul>
          {chatLog.map((msg, idx) => (
            <li key={idx}>
              <p><strong>Text:</strong> {msg.text}</p>
              <p><strong>Sentiment:</strong> {JSON.stringify(msg.sentiment)}</p>
              <p><strong>Keywords:</strong> {JSON.stringify(msg.keywords)}</p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
