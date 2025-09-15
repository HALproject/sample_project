import React, { useEffect, useRef } from "react";

export default function ResultViewer({ results, partialText }) {
  const lastAudioRef = useRef(null);

  // 新しい結果が追加されたら音声再生
  useEffect(() => {
    if (results.length === 0) return;

    const lastResult = results[results.length - 1];

    if (lastResult.audio) {
      const binary = atob(lastResult.audio);
      const buffer = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) {
        buffer[i] = binary.charCodeAt(i);
      }
      const blob = new Blob([buffer], { type: "audio/wav" });
      const url = URL.createObjectURL(blob);

      // 以前のAudioがあれば停止
      if (lastAudioRef.current) {
        lastAudioRef.current.pause();
        lastAudioRef.current.src = "";
      }

      const audio = new Audio(url);
      lastAudioRef.current = audio;
      audio.play().catch((err) => console.error("Audio playback failed:", err));
    }
  }, [results]);

  return (
    <div className="p-4 border rounded mt-2 max-h-[400px] overflow-y-auto">
      <h2 className="font-bold mb-2">Conversation</h2>
      <ul className="space-y-2">
        {/* 過去の結果 */}
        {results.map((r, idx) => (
          <li
            key={idx}
            className={
              r.sender === "assistant"
                ? "text-blue-600 bg-blue-100 p-2 rounded"
                : "text-gray-800 bg-gray-100 p-2 rounded"
            }
          >
            <div>
              <strong>{r.sender}:</strong> {r.text}
            </div>
            {r.time_stamp && (
              <div className="text-xs text-gray-500 mt-1">
                {r.time_stamp} {r.demo_pattern_name ? `(${r.demo_pattern_name})` : ""}
              </div>
            )}
          </li>
        ))}

        {/* リアルタイム部分テキスト */}
        {partialText && (
          <li className="text-gray-500 italic p-2 rounded border-dashed border-2 border-gray-300">
            <strong>Listening:</strong> {partialText}
          </li>
        )}
      </ul>
    </div>
  );
}
