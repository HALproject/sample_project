from fastapi import FastAPI
from speech_recognizer import SpeechRecognizer

app = FastAPI()
recognizer = SpeechRecognizer("config.yaml")

@app.post("/config/reload")
def reload_config():
    recognizer.reload_config()
    return {"status": "reloaded", "config": recognizer.cfg}
