# sample_project



- 4モード（雑談 / アラート / タイマー / レポート）対応
- プロンプトは外部YAMLで管理（config/prompts.yaml）
- 音声入力はフロント→WebSocketで常時送信（バイナリ）。サーバ側で ffmpeg 変換→Whisper streaming（ローカルモデル）で文字起こし
- 音声コマンドでモード切替・選択画面に戻る・会話終了に対応
- 会話履歴はモード別に保持、レポートでサマリ可
- OpenAIチャットモデルは動的切替（HTTP APIで変更）。Whisperモデルもリロード対応（ローカル backend/models/whisper/<model_name> から読み込み）
- ESPnet2 TTSは起動時固定ロード（CPU開発、本番GPU切替は環境変数で）
- 応答は テキスト＋Base64 WAV をWebSocketで返却

```bash
cd backend
python -m venv env
source env/bin/activate

pip install -r requirements.txt

# ffmpeg をOS側に
sudo apt update
sudo apt install -y ffmpeg

# 環境変数
export OPENAI_API_KEY="sk-xxxx"
export OPENAI_MODEL="gpt-4o"
export ESPNET_MODEL_TAG="kan-bayashi/ljspeech_vits"
export ESPNET_DEVICE="cpu"        # 本番では "cuda" 想定
export WHISPER_MODEL_NAME="small" # 例：backend/models/whisper/small

# 起動
uvicorn app:app --reload --host 0.0.0.0 --port 8000


```

# 実装メモ / 補足
- ffmpeg 変換は webm/opus → wav(16k/mono) に統一し Whisper に渡しています。
- whisper-streaming の Transcriber 仕様はバージョン差があるため、whisper_manager.py の Transcriber(...) 引数（model_path=...）と transcribe(...) の戻り値の取り出しは、手元のバージョンに合わせて微調整してください。
- 音声コマンドは単純なキーワード一致です。必要なら正規表現・スロット/インテント検出を拡張してください。
- セッション保持はWS接続単位の簡易辞書です。プロダクションでは外部ストアやユーザID紐づけを検討してください。
- TTSはESPnet2起動時固定ロード。モデル切替は想定していません（要件通り）。
- OpenAIモデル／Whisperモデルは /api/change_models で変更できます（UIから叩いてください）。
- レポートモードのサマリは、ユーザ発話に「サマリ/サマリー」が含まれると summary_prompt を追記して要約に誘導します。

