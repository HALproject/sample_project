import React, { useEffect, useRef, useState } from "react";

export default function Transcriber() {
  const [messages, setMessages] = useState([]);
  const [liveText, setLiveText] = useState("");

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/audio");

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.final) {
        // 確定 → チャットログに追加
        setMessages((prev) => [...prev, msg.text]);
        setLiveText("");
      } else {
        // 途中経過 → 逐次上書き
        setLiveText(msg.text);
      }
    };

    return () => ws.close();
  }, []);

  return (
    <div>
      <div>
        {messages.map((m, i) => (
          <p key={i}>{m}</p>
        ))}
      </div>
      <div style={{ color: "gray" }}>
        {liveText && <p>▶ {liveText}</p>}
      </div>
    </div>
  );
}
