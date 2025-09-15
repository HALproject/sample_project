import logging
import numpy as np
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from app import config
from app.utils.functions import Function
from app.app_core import app

router = APIRouter()
function = Function()

# セッション管理
sessions: Dict[int, Dict[str, Any]] = {}

# 定数 (configに移行予定)
SOUND_GET_DURATION_SEC = 7.0
SILENCE_THRESHOLD_DB = -60.0
SAMPLE_RATE = 16000  # whisper-manager が想定しているサンプルレート


@router.post("/init_ws")
async def init_ws():
    """UI初期化時に呼ばれる"""
    app.state.flg_running = False
    app.state.flg_recording = False
    return JSONResponse({"status": "initialized"})


@router.post("/start_ws")
async def start_ws():
    """UIから録音開始"""
    app.state.flg_running = True
    app.state.flg_recording = True
    return JSONResponse({"status": "recording started"})


@router.post("/stop_ws")
async def stop_ws():
    """UIから録音停止"""
    app.state.flg_running = False
    app.state.flg_recording = False
    return JSONResponse({"status": "recording stopped"})


@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    sid = id(ws)
    logging.info(f"ws connected: {sid}")

    sessions[sid] = {
        "elapsed_sec": 0.0,
    }

    try:
        while True:
            if not app.state.flg_running or not app.state.flg_recording:
                await ws.send_json({"status": "idle"})
                continue

            # --- 音声受信 ---
            data = await ws.receive_bytes()
            audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

            # --- 無音判定 ---
            if function.is_silence(audio, threshold_db=SILENCE_THRESHOLD_DB):
                continue

            # --- whisper_manager に渡す ---
            app.state.whisper_manager.insert_audio(audio)

            # 経過時間を加算
            sessions[sid]["elapsed_sec"] += len(audio) / SAMPLE_RATE

            formatted_date = function.get_timestamp()

            # --- SOUND_GET_DURATION_SEC 未満 → 部分結果を返す ---
            if sessions[sid]["elapsed_sec"] < SOUND_GET_DURATION_SEC:
                response = app.state.whisper_manager.get_result()
                if response:
                    beg, end, text = response
                    if text:
                        await ws.send_json({
                            "session_id": sid,
                            "sender": "user",
                            "text": text,
                            "time_stamp": formatted_date,
                            "status": "partial",
                        })
                continue

            # --- SOUND_GET_DURATION_SEC を超えたら finish ---
            result = app.state.whisper_manager.finish()  # (b, e, t)
            if result:
                beg, end, text = result
                await ws.send_json({
                    "session_id": sid,
                    "sender": "user",
                    "text": text,
                    "time_stamp": formatted_date,
                    "status": "final",
                })

                # --- OpenAI 応答 ---
                system_text = config["modes"]["mode_selection"].get("system", "")
                answer_text = function.get_openai_answer(
                    system_content=system_text,
                    text=text,
                    llm=app.state.openai_manager
                )

                if answer_text:
                    # 履歴保存
                    function.text_history(
                        file_path=config["text_history"],
                        role="user",
                        text=text,
                        timestamp=formatted_date,
                    )
                    function.text_history(
                        file_path=config["text_history"],
                        role="assistant",
                        text=answer_text,
                        timestamp=formatted_date,
                    )

                    # TTS
                    try:
                        audio_b64 = await app.state.tts_manager.synthesize_to_b64(answer_text)
                    except Exception as e:
                        audio_b64 = None
                        logging.error(f"TTS Error: {e}")

                    await ws.send_json({
                        "session_id": sid,
                        "sender": "assistant",
                        "text": answer_text,
                        "time_stamp": formatted_date,
                        "audio": audio_b64,
                        "status": "answer",
                    })

            # --- サイクルリセット ---
            sessions[sid]["elapsed_sec"] = 0.0
            app.state.whisper_manager.reset()

    except WebSocketDisconnect:
        logging.info(f"ws disconnected: {sid}")
        sessions.pop(sid, None)
    except Exception as e:
        logging.error(f"ASR Error: {e}")
        try:
            await ws.send_json({"type": "error", "text": f"ASR Error:{e}"})
        except RuntimeError:
            logging.info("WebSocket was already closed.")
