# backend/models/whisper_manager.py
import asyncio
import os
import tempfile
from typing import Optional

class WhisperManager:
    """
    backend/models/whisper/<model_name> に配置済みのローカルモデルをロードして使用。
    受信バイト(webm/opus想定)は ffmpeg で 16kHz/mono WAV に変換後、Transcriber へ。
    """
    def __init__(self, models_base_path: str = "backend/models/whisper"):
        self.models_base_path = models_base_path
        self.transcriber = None
        self.model_name: Optional[str] = None
        self.model_path: Optional[str] = None
        self._lock = asyncio.Lock()

    async def load(self, model_name: str = "small"):
        from whisper_streaming import Transcriber  # 遅延import
        async with self._lock:
            model_dir = os.path.join(self.models_base_path, model_name)
            if not os.path.isdir(model_dir):
                raise FileNotFoundError(f"Whisper model not found: {model_dir}")

            # 以前のモデルのクリーンアップが必要ならここで実施
            self.transcriber = await asyncio.get_event_loop().run_in_executor(
                None, lambda: Transcriber(model_path=model_dir, vad=True)
            )
            self.model_name = model_name
            self.model_path = model_dir

    async def _convert_to_wav(self, webm_bytes: bytes) -> bytes:
        """
        webm/opus → wav(16kHz/mono) へ変換してバイト列で返す
        """
        import asyncio as aio
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as fin:
            fin.write(webm_bytes)
            fin.flush()
            in_path = fin.name
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fout:
            out_path = fout.name

        cmd = [
            "ffmpeg", "-y",
            "-i", in_path,
            "-ar", "16000",
            "-ac", "1",
            out_path
        ]
        proc = await aio.create_subprocess_exec(
            *cmd, stdout=aio.subprocess.PIPE, stderr=aio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        try:
            os.remove(in_path)
        finally:
            pass
        if proc.returncode != 0:
            try:
                os.remove(out_path)
            finally:
                pass
            raise RuntimeError(f"ffmpeg conversion failed: {stderr.decode(errors='ignore')}")

        try:
            with open(out_path, "rb") as f:
                wav_bytes = f.read()
        finally:
            os.remove(out_path)
        return wav_bytes

    async def transcribe_bytes(self, audio_bytes: bytes) -> str:
        """
        受信バイト（webm/opus想定）→ ffmpeg変換 → 一時wav → Transcriber.transcribe()
        """
        async with self._lock:
            if self.transcriber is None:
                raise RuntimeError("Whisper model not loaded.")

            wav_bytes = await self._convert_to_wav(audio_bytes)

            # Transcriberはファイルパス入力が安定なので一時ファイル経由
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(wav_bytes)
                tmp.flush()
                wav_path = tmp.name

            try:
                # whisper-streaming の戻り値仕様に合わせて取り出し
                result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.transcriber.transcribe(wav_path)
                )
                if isinstance(result, dict):
                    return result.get("text", "")
                return str(result)
            finally:
                try:
                    os.remove(wav_path)
                except Exception:
                    pass
