// src/components/ChatView.jsx
// チャット画面本体
import React, { useRef, useEffect } from "react";

export default function ChatView({
  messages,
  ephemeralTranscript,
  onSendText,
  keyboardMode,
  setKeyboardMode,
  onGoHome
}) {
  const endRef = useRef(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, ephemeralTranscript]);

  return (
    <section className="chat">
      <div className="chat-header">
        <button className="ghost" onClick={onGoHome}>← 選択画面に戻る</button>
        <div className="grow" />
        <label className="toggle">
          <input
            type="checkbox"
            checked={keyboardMode}
            onChange={(e) => setKeyboardMode(e.target.checked)}
          />
          キーボード入力
        </label>
      </div>

      <div className="chat-body">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`bubble ${m.role === "user" ? "user" : "assistant"}`}
          >
            {m.content}
          </div>
        ))}
        {ephemeralTranscript ? (
          <div className="bubble user ephemeral">{ephemeralTranscript}</div>
        ) : null}
        <div ref={endRef} />
      </div>

      {keyboardMode && (
        <KeyboardInput onSend={onSendText} />
      )}
    </section>
  );
}

function KeyboardInput({ onSend }) {
  const [text, setText] = React.useState("");
  return (
    <div className="keyboard">
      <textarea
        rows={2}
        placeholder="メッセージを入力…"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
            onSend(text);
            setText("");
          }
        }}
      />
      <button
        onClick={() => {
          onSend(text);
          setText("");
        }}
      >送信</button>
      <span className="hint">Ctrl/⌘ + Enter で送信</span>
    </div>
  );
}
