// src/App.jsx
// アプリ統括。WS接続・音声送信・イベント処理
import React from "react";
import "./styles.css";
import AutoReconnectWS from "./ws/AutoReconnectWS";
import AudioRecorder from "./audio/AudioRecorder";
import { playBase64Wav } from "./utils/audio";
import Sidebar from "./components/Sidebar";
import ChatView from "./components/ChatView";
import ModelPanel from "./components/ModelPanel";

const WS_URL = (location.protocol === "https:" ? "wss://" : "ws://") + location.host.replace(/\/$/, "") + "/ws";

export default function App() {
  const [wsReady, setWsReady] = React.useState(false);
  const [currentMode, setCurrentMode] = React.useState(null);
  const [showSidebar, setShowSidebar] = React.useState(true);
  const [keyboardMode, setKeyboardMode] = React.useState(false);
  const [messages, setMessages] = React.useState([]); // {role, content}
  const [ephemeralTranscript, setEphemeralTranscript] = React.useState("");
  const [status, setStatus] = React.useState(null);

  const wsRef = React.useRef(null);
  const recRef = React.useRef(null);

  React.useEffect(() => {
    // 初期ステータス取得
    fetch("/api/status").then(r => r.json()).then(setStatus).catch(() => {});
  }, []);

  React.useEffect(() => {
    // WS接続
    const ws = new AutoReconnectWS(WS_URL, {
      onOpen: () => setWsReady(true),
      onClose: () => setWsReady(false),
      onMessage: (e) => handleWSMessage(e),
      onError: () => {}
    });
    wsRef.current = ws;

    // マイク開始（許可が必要）
    const rec = new AudioRecorder({
      chunkMs: 300,
      onData: (buf) => {
        if (wsRef.current?.ready) wsRef.current.send(buf);
      }
    });
    rec.start().catch((err) => {
      console.error("Mic start failed:", err);
      alert("マイクの使用を許可してください。");
    });
    recRef.current = rec;

    return () => {
      ws.close();
      rec.stop();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleWSMessage(e) {
    try {
      const msg = JSON.parse(e.data);
      switch (msg.type) {
        case "mode_changed":
          setCurrentMode(msg.mode);
          setShowSidebar(false);
          setMessages((prev) => [...prev, { role: "assistant", content: msg.text }]);
          if (msg.audio) playBase64Wav(msg.audio); // モード切替の音声再生
          setEphemeralTranscript("");
          break;
        case "transcript":
          setEphemeralTranscript(msg.text);
          break;
        case "chat_response":
          setMessages((prev) => [...prev, { role: "assistant", content: msg.text }]);
          if (msg.audio) playBase64Wav(msg.audio);
          setEphemeralTranscript("");
          break;
        case "chat_ended":
          setMessages((prev) => [...prev, { role: "assistant", content: msg.text }]);
          setCurrentMode(null);
          setShowSidebar(true);
          setEphemeralTranscript("");
          break;
        case "go_home":
          setCurrentMode(null);
          setShowSidebar(true);
          setEphemeralTranscript("");
          break;
        case "error":
          setMessages((prev) => [...prev, { role: "assistant", content: `⚠️ ${msg.text}` }]);
          break;
        default:
          // noop
          break;
      }
    } catch {
      // 非JSONは無視
    }
  }

  function selectMode(mode) {
    if (!wsRef.current?.ready) return;
    wsRef.current.send(JSON.stringify({ type: "set_mode", mode }));
  }

  function sendTextMessage(text) {
    if (!text?.trim()) return;
    if (!wsRef.current?.ready) return;
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    wsRef.current.send(JSON.stringify({ type: "chat", text }));
  }

  async function changeModels(payload) {
    const res = await fetch("/api/change_models", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const s = await res.json();
    setStatus((prev) => ({ ...prev, ...s }));
  }

  return (
    <div className="layout">
      <Sidebar
        currentMode={currentMode}
        onSelectMode={selectMode}
        visible={showSidebar}
      />

      <main className={`content ${showSidebar ? "sidebar-open" : "sidebar-closed"}`}>
        <header className="topbar">
          <div className="left">
            <button className="ghost" onClick={() => setShowSidebar((v) => !v)}>
              {showSidebar ? "▶ チャットへ" : "◀ モード選択"}
            </button>
          </div>
          <div className="center">
            <strong>{currentMode ? `モード: ${currentMode}` : "モードを選択してください"}</strong>
            <span className={`badge ${wsReady ? "ok" : "ng"}`}>
              {wsReady ? "WS 接続中" : "再接続中…"}
            </span>
          </div>
          <div className="right" />
        </header>

        {!showSidebar && (
          <ChatView
            messages={messages}
            ephemeralTranscript={ephemeralTranscript}
            onSendText={sendTextMessage}
            keyboardMode={keyboardMode}
            setKeyboardMode={setKeyboardMode}
            onGoHome={() => {
              // フロントから戻る操作。サーバへ go_home を強制してもOKだがここはUIのみ
              setCurrentMode(null);
              setShowSidebar(true);
            }}
          />
        )}

        <ModelPanel status={status} onChange={changeModels} />
      </main>
    </div>
  );
}
