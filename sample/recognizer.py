from whisper_streaming import FasterWhisperASR
import asyncio

class AudioRecognizer:
    def __init__(self, config_path: str):
        self.config = self.load_config(config_path)
        self.model_name = self.config["model"]
        self.asr = FasterWhisperASR(model=self.model_name)
        self.vad_enabled = self.config.get("vad", True)
        self.lock = asyncio.Lock()

    def load_config(self, path):
        # yaml読み込み処理
        pass

    async def switch_model(self, new_model: str):
        async with self.lock:
            # バッファを処理しきる
            await self.flush()
            # モデル切替
            self.asr = FasterWhisperASR(model=new_model)
            self.model_name = new_model

    def set_vad(self, enable: bool):
        self.vad_enabled = enable

    async def process_audio_chunk(self, pcm_bytes: bytes):
        # PCM -> asr.feed() 的な流れ
        text = self.asr.transcribe_chunk(pcm_bytes, vad=self.vad_enabled)
        return text

    async def flush(self):
        # バッファ残りを処理して確定出力
        return self.asr.flush()