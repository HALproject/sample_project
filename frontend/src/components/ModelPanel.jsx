// src/components/ModelPanel.jsx
// モデル切替UI
import React from "react";

export default function ModelPanel({ status, onChange }) {
  const [openaiModel, setOpenaiModel] = React.useState("");
  const [whisperModel, setWhisperModel] = React.useState("");

  React.useEffect(() => {
    if (!status) return;
    setOpenaiModel(status.openai_model || "");
    setWhisperModel(status.whisper_model || "");
  }, [status]);

  return (
    <div className="panel">
      <h3>モデル設定</h3>
      <div className="row">
        <label>OpenAIモデル</label>
        <input value={openaiModel} onChange={(e) => setOpenaiModel(e.target.value)} />
      </div>
      <div className="row">
        <label>Whisperモデル</label>
        <input value={whisperModel} onChange={(e) => setWhisperModel(e.target.value)} />
      </div>
      <div className="row">
        <button onClick={() => onChange({ openai_model: openaiModel, whisper_model: whisperModel })}>
          変更を反映
        </button>
      </div>
      {status && (
        <div className="status">
          <div>ESPnet: {status.espnet_model} ({status.espnet_device})</div>
          <div>利用可能モード: {status.modes?.join(" / ")}</div>
        </div>
      )}
    </div>
  );
}
