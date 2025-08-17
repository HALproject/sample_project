# backend/app.py
import os
import json
import yaml
from typing import Dict, Any, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from models.tts_espnet import TTSManager
from models.whisper_manager import WhisperManager

# ====== 環境変数 ======
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Set OPENAI_API_KEY")

# OpenAI SDK v1
from openai import OpenAI
openai_client = OpenAI(api_key=OPENAI_API_KEY)

DEFAULT_OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
ESPNET_MODEL_TAG = os.environ.get("ESPNET_MODEL_TAG", "kan-bayashi/ljspeech_vits")
ESPNET_DEVICE = os.environ.get("ESPNET_DEVICE", "cpu")
DEFAULT_WHISPER_MODEL = os.environ.get("WHISPER_MODEL_NAME", "small")

# ====== プロンプト読込 ======
with open(os.path.join("backend", "config", "prompts.yaml"), "r", encoding="utf-8") as f:
    PROMPTS = yaml.safe_load(f)
MODES = list(PROMPTS["modes"].keys())  # ["雑談","アラート","タイマー","レポート"]

# ====== アプリ初期化 ======
app = FastAPI(title="Voice Chat Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# ====== モデル管理 ======
tts_manager = TTSManager(model_tag=ESPNET_MODEL_TAG, device=ESPNET_DEVICE)
whisper_manager = WhisperManager()
current_openai_model = DEFAULT_OPENAI_MODEL

@app.on_event("startup")
async def startup():
    # ESPnet2 TTS 起動時ロード（固定）
    tts_manager.load()
    # Whisper streaming ローカルモデルロード
    await whisper_manager.load(DEFAULT_WHISPER_MODEL)

# ====== セッション管理 ======
# sessions[ws_id]: { "<mode>": [msgs...], "current_mode": "雑談"/None }
sessions: Dict[int, Dict[str, Any]] = {}

def build_messages(mode: str, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    sys_prompt = PROMPTS["modes"][mode].get("system", "")
    return [{"role": "system", "content": sys_prompt}] + history

def detect_voice_command(text: str):
    """
    音声コマンド検出（単純一致）
    - モード切替: 「雑談モード / アラートモード / タイマーモード / レポートモード」
    - 終了: 「会話終了」「チャットを終了して」
    - 戻る: 「選択画面に戻って」「モード選択に戻って」
    """
    mapping = {
        "雑談モード": {"type": "switch_mode", "mode": "雑談"},
        "アラートモード": {"type": "switch_mode", "mode": "アラート"},
        "タイマーモード": {"type": "switch_mode", "mode": "タイマー"},
        "レポートモード": {"type": "switch_mode", "mode": "レポート"},
        "会話終了": {"type": "end_chat"},
        "チャットを終了して": {"type": "end_chat"},
        "選択画面に戻って": {"type": "go_home"},
        "モード選択に戻って": {"type": "go_home"},
    }
    for k, v in mapping.items():
        if k in text:
            return v
    return None

async def send_mode_start(ws: WebSocket, sid: int, mode: str):
    conf = PROMPTS["modes"].get(mode, {})
    text = conf.get("initial_scenario", "")
    sessions[sid][mode].append({"role": "assistant", "content": text})
    audio_b64 = await tts_manager.synthesize_to_b64(text)
    await ws.send_json({
        "type": "mode_changed",
        "mode": mode,
        "text": text,
        "audio": audio_b64
    })

async def call_openai(messages: List[Dict[str, str]]) -> str:
    # OpenAI Chat（v1 client）
    completion = openai_client.chat.completions.create(
        model=current_openai_model,
        messages=messages,
        temperature=0.7,
    )
    return completion.choices[0].message.content

# ====== WebSocket ======
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    sid = id(ws)
    sessions[sid] = {m: [] for m in MODES}
    sessions[sid]["current_mode"] = None

    try:
        while True:
            msg = await ws.receive()

            # ---- 音声バイナリ ----
            if "bytes" in msg and msg["bytes"] is not None:
                chunk = msg["bytes"]

                # Whisper でASR
                try:
                    text = await whisper_manager.transcribe_bytes(chunk)
                except Exception as e:
                    await ws.send_json({"type": "error", "text": f"ASR error: {e}"})
                    continue

                if not text:
                    continue

                # 音声コマンド判定
                cmd = detect_voice_command(text)
                if cmd:
                    if cmd["type"] == "switch_mode":
                        mode = cmd["mode"]
                        sessions[sid]["current_mode"] = mode
                        await send_mode_start(ws, sid, mode)
                    elif cmd["type"] == "end_chat":
                        cur = sessions[sid]["current_mode"]
                        if cur:
                            sessions[sid][cur] = []
                        sessions[sid]["current_mode"] = None
                        await ws.send_json({"type": "chat_ended", "text": "会話を終了しました"})
                    elif cmd["type"] == "go_home":
                        sessions[sid]["current_mode"] = None
                        await ws.send_json({"type": "go_home"})
                    continue

                # 普通の逐次テキスト（UI表示用）
                await ws.send_json({"type": "transcript", "text": text})
                continue

            # ---- テキスト（JSON想定）----
            if "text" in msg and msg["text"]:
                raw = msg["text"]
                try:
                    data = json.loads(raw)
                except Exception:
                    await ws.send_json({"type": "error", "text": "invalid json"})
                    continue

                typ = data.get("type")

                if typ == "set_mode":
                    mode = data.get("mode")
                    if mode in MODES:
                        sessions[sid]["current_mode"] = mode
                        await send_mode_start(ws, sid, mode)
                    else:
                        await ws.send_json({"type": "error", "text": f"unknown mode: {mode}"})
                    continue

                if typ == "chat":
                    cur = sessions[sid]["current_mode"]
                    if not cur:
                        await ws.send_json({"type": "error", "text": "モードが選択されていません"})
                        continue
                    user_text = data.get("text", "")
                    sessions[sid][cur].append({"role": "user", "content": user_text})

                    messages = build_messages(cur, sessions[sid][cur])

                    # レポートモードで「サマリ」指示があればサマリ用プロンプトを追加
                    if cur == "レポート" and ("サマリ" in user_text or "サマリー" in user_text):
                        summary_prompt = PROMPTS["modes"][cur].get("summary_prompt", "")
                        messages.append({"role": "user", "content": summary_prompt})

                    # OpenAI
                    try:
                        ai_text = await call_openai(messages)
                    except Exception as e:
                        await ws.send_json({"type": "error", "text": f"OpenAI error: {e}"})
                        continue

                    sessions[sid][cur].append({"role": "assistant", "content": ai_text})

                    # TTS
                    try:
                        audio_b64 = await tts_manager.synthesize_to_b64(ai_text)
                    except Exception as e:
                        audio_b64 = None

                    await ws.send_json({
                        "type": "chat_response",
                        "mode": cur,
                        "text": ai_text,
                        "audio": audio_b64
                    })
                    continue

                # 未知のタイプ
                await ws.send_json({"type": "error", "text": f"unknown message type: {typ}"})

    except WebSocketDisconnect:
        sessions.pop(sid, None)

@app.post("/api/change_models")
async def change_models(req: Request):
    """
    JSON 例:
    {
      "openai_model": "gpt-4o",
      "whisper_model": "medium"
    }
    """
    global current_openai_model
    body = await req.json()
    updated = {}

    if "openai_model" in body and body["openai_model"]:
        current_openai_model = body["openai_model"]
        updated["openai_model"] = current_openai_model

    if "whisper_model" in body and body["whisper_model"]:
        await whisper_manager.load(body["whisper_model"])
        updated["whisper_model"] = whisper_manager.model_name

    return {"status": "ok", **updated}

@app.get("/api/status")
async def status():
    return {
        "openai_model": current_openai_model,
        "whisper_model": whisper_manager.model_name,
        "espnet_model": ESPNET_MODEL_TAG,
        "espnet_device": ESPNET_DEVICE,
        "modes": MODES
    }