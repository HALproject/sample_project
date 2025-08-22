async def handle_stream(ws, recognizer):
    while True:
        data = await ws.receive_bytes()
        text = await recognizer.process_audio_chunk(data)
        if text:
            await ws.send_text(text)