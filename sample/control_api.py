from fastapi import FastAPI, WebSocket
from websocket_handler import handle_stream
from recognizer import AudioRecognizer
import yaml

app = FastAPI()
recognizer = AudioRecognizer(config_path="config.yaml")

@app.post("/config/model")
async def set_model(model_name: str):
    await recognizer.switch_model(model_name)
    return {"status": "ok", "model": model_name}

@app.post("/config/vad")
async def set_vad(enable: bool):
    recognizer.set_vad(enable)
    return {"status": "ok", "vad": enable}

@app.websocket("/stream")
async def stream_endpoint(ws: WebSocket):
    await ws.accept()
    await handle_stream(ws, recognizer)