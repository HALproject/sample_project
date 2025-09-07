import numpy as np
from fastapi import WebSocket

@app.websocket("/ws/audio")
async def audio_stream(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_bytes()
            audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

            recognizer.insert_audio(audio)
            result = recognizer.get_result()

            if result:
                beg, end, text = result
                await ws.send_json({
                    "text": text,
                    "final": recognizer.is_final()
                })
    except Exception:
        await ws.close()

# import numpy as np
# from fastapi import FastAPI, WebSocket
# from speech_recognizer import SpeechRecognizer

# app = FastAPI()
# recognizer = SpeechRecognizer("config.yaml")  # 起動時に一度だけ初期化

# @app.websocket("/ws/audio")
# async def audio_stream(ws: WebSocket):
#     await ws.accept()
#     try:
#         while True:
#             data = await ws.receive_bytes()
#             audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

#             recognizer.insert_audio(audio)
#             result = recognizer.get_result()

#             if result:
#                 beg, end, text = result
#                 await ws.send_json({
#                     "text": text,
#                     "final": recognizer.is_final()
#                 })
#     except Exception as e:
#         print("WebSocket closed:", e)
#         await ws.close()
