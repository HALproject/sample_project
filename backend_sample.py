import io
import torch
import torchaudio
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from faster_whisper import WhisperModel
from silero_vad import get_speech_timestamps
from contextlib import asynccontextmanager
from transformers import pipeline

# -------------------------
# 設定パラメータ
# -------------------------
MODEL_SIZE = "small"
DEVICE = "cpu"           # "cuda" も可
COMPUTE_TYPE = "int8"

VAD_THRESHOLD = 0.5
VAD_MIN_SPEECH_SEC = 0.3
SAMPLE_RATE = 16000

# -------------------------
# Whisper 初期化
# -------------------------
whisper = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)

# -------------------------
# Silero VAD 初期化
# -------------------------
vad_model, utils = torch.hub.load(
    repo_or_dir="snakers4/silero-vad",
    model="silero_vad",
    force_reload=False
)
(get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils

# -------------------------
# Sentiment / Keywords (HuggingFace Transformers)
# -------------------------
sentiment_analyzer = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")
keyword_extractor = pipeline("feature-extraction")  # 単純例、カスタムでTF-IDFやKeyBERTを使ってもOK

# -------------------------
# VAD 処理クラス
# -------------------------
class VADProcessor:
    def __init__(self, vad_model, threshold=0.5, min_speech_sec=0.3, sr=16000):
        self.vad_model = vad_model
        self.threshold = threshold
        self.min_speech_sec = min_speech_sec
        self.sr = sr

    def get_segments(self, audio_tensor):
        timestamps = get_speech_timestamps(audio_tensor, self.vad_model, sampling_rate=self.sr, threshold=self.threshold)
        filtered = [seg for seg in timestamps if (seg["end"] - seg["start"]) / self.sr >= self.min_speech_sec]
        return filtered

vad_processor = VADProcessor(vad_model, threshold=VAD_THRESHOLD, min_speech_sec=VAD_MIN_SPEECH_SEC, sr=SAMPLE_RATE)

# -------------------------
# FastAPI サーバー
# -------------------------
app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Backend started.")
    yield
    print("Backend stopped.")

# -------------------------
# WebSocket エンドポイント
# -------------------------
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    buffer = torch.tensor([], dtype=torch.float32)

    try:
        async for message in ws.iter_bytes():
            # PCM float32 に変換
            audio_chunk, sr = torchaudio.load(io.BytesIO(message))
            buffer = torch.cat((buffer, audio_chunk.squeeze()), dim=0)

            # VADで発話区間取得
            segments = vad_processor.get_segments(buffer)

            for seg in segments:
                speech_tensor = buffer[seg["start"]:seg["end"]]

                # Whisper で文字起こし
                segments_whisper, _ = whisper.transcribe(speech_tensor.numpy(), language="auto")

                # partial 送信（逐次）
                for seg_w in segments_whisper:
                    await ws.send_json({
                        "type": "partial",
                        "text": seg_w.text,
                        "timestamp": seg_w.start
                    })

                # final 確定
                final_text = " ".join([seg_w.text for seg_w in segments_whisper])

                # sentiment分析
                sentiment_result = sentiment_analyzer(final_text)
                # キーワード抽出（ここでは単純に feature-extraction 例）
                keywords_vector = keyword_extractor(final_text)
                # 実際のキーワード抽出は別ライブラリ(KeyBERTなど)推奨

                await ws.send_json({
                    "type": "final",
                    "text": final_text,
                    "timestamp": seg["end"],
                    "sentiment": sentiment_result,
                    "keywords": keywords_vector
                })

            # 処理済みバッファを削除
            if segments:
                last_end = segments[-1]["end"]
                buffer = buffer[last_end:]

    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"Error: {e}")
