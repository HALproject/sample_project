import React, { useState } from "react";
import ControlPanel from "./components/ControlPanel";
import ResultViewer from "./components/ResultViewer";

export default function App() {
  const [results, setResults] = useState([]);
  const [partialText, setPartialText] = useState(""); // リアルタイムテキスト

  const handleResult = (msg) => {
    // msg が部分テキストか最終回答かで分岐
    if (msg.status==="partial") {
      // 部分テキストの場合は partialText に設定
      setPartialText(msg.text);
    } else {
      // 最終回答の場合は results に追加
      setResults((prev) => [...prev, msg]);
      // リアルタイムテキストをクリア
      setPartialText("");
    }
  };

  return (
    <div className="max-w-lg mx-auto mt-10">
      <h1 className="text-2xl font-bold mb-4">Realtime Whisper Chat</h1>
      <ControlPanel onResult={handleResult} />
      <ResultViewer results={results} partialText={partialText} />
    </div>
  );
}
