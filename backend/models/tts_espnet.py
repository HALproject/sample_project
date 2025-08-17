# backend/models/tts_espnet.py
import os
import base64
import tempfile
import soundfile as sf
import torch
import asyncio
from espnet2.bin.tts_inference import Text2Speech

class TTSManager:
    def __init__(self, model_tag: str, device: str = "cpu"):
        self.model_tag = model_tag
        self.device = device
        self.tts = None

    def load(self):
        self.tts = Text2Speech.from_pretrained(
            model_tag=self.model_tag,
            device=self.device,
        )

    def synthesize_wav_bytes(self, text: str, sample_rate=22050) -> bytes:
        if self.tts is None:
            raise RuntimeError("TTS not loaded.")
        with torch.no_grad():
            wav = self.tts(text)["wav"].view(-1).cpu().numpy()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpf:
            sf.write(tmpf.name, wav, sample_rate)
            path = tmpf.name
        with open(path, "rb") as f:
            data = f.read()
        os.remove(path)
        return data

    async def synthesize_to_b64(self, text: str) -> str:
        loop = asyncio.get_event_loop()
        wav_bytes = await loop.run_in_executor(None, self.synthesize_wav_bytes, text)
        return base64.b64encode(wav_bytes).decode("utf-8")
