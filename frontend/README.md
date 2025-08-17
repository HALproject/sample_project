# 使い方メモ

フロント起動: npm i → npm run dev（Vite標準）

- バックエンドは前回ご提供のFastAPIを localhost:8000 で起動。
- フロントを localhost:5173 などで動かす場合は、WS_URL を ws://localhost:8000/ws に変えてください（本番は同一オリジン想定で現状コードのままOK）。
- 画面起動→自動でマイク許可→WS接続&常時送信→サーバ側でASR→音声コマンド（「雑談モード」「選択画面に戻って」「会話終了」など）でUIが切り替わり、モード切替のTTS音声も mode_changed 受信時に自動再生します。
- キーボード入力に切り替えるスイッチあり（Ctrl/⌘+Enter送信）。
- 下部の モデル設定 から /api/change_models を叩き、OpenAI/Whisperモデルをライブ切替できます（次回以降の処理に反映）。