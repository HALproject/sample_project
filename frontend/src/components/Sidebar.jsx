// src/components/Sidebar.jsx
// 4モード選択＋表示切替
import React from "react";

const modes = ["雑談", "アラート", "タイマー", "レポート"];

export default function Sidebar({ currentMode, onSelectMode, visible }) {
  return (
    <aside className={`sidebar ${visible ? "visible" : ""}`}>
      <h2>モード選択</h2>
      <div className="mode-grid">
        {modes.map((m) => (
          <button
            key={m}
            className={`mode-btn ${currentMode === m ? "active" : ""}`}
            onClick={() => onSelectMode(m)}
          >
            {m}
          </button>
        ))}
      </div>
      <p className="hint">※ 音声コマンドでも切替可能です</p>
    </aside>
  );
}
