import yaml
import threading
from whisper_online import FasterWhisperASR, VACOnlineASRProcessor

class SpeechRecognizer:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.lock = threading.Lock()
        self._load_and_init()

    def _load_and_init(self):
        """config.yaml を読み込んで ASR/VAD を初期化"""
        with open(self.config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        self.cfg = cfg

        # ASRモデル初期化
        self.asr = FasterWhisperASR(
            lan=cfg["asr"]["language"],
            modelsize=cfg["asr"]["model"],
            device=cfg["asr"]["device"]
        )

        if cfg.get("vad", {}).get("enabled", True):
            self.asr.use_vad()

        # VAD付きオンラインASR
        self.online = VACOnlineASRProcessor(
            online_chunk_size=cfg["vad"]["chunk_size"],
            asr=self.asr,
            tokenizer=None,
            buffer_trimming=tuple(cfg["vad"]["buffer_trimming"]),
            min_silence_duration_ms=cfg["vad"]["silence_ms"]
        )

    def reload_config(self):
        """config.yaml を再読み込みして再初期化"""
        with self.lock:
            self._load_and_init()
            print("SpeechRecognizer reloaded with new config:", self.cfg)

    def insert_audio(self, audio_chunk):
        """音声チャンクを追加"""
        with self.lock:
            self.online.insert_audio_chunk(audio_chunk)

    def get_result(self):
        """結果を取得"""
        with self.lock:
            return self.online.process_iter()

    def is_final(self):
        """最後の結果が確定かどうか"""
        with self.lock:
            return self.online.is_currently_final

    def finish(self):
        """最終処理"""
        with self.lock:
            return self.online.finish()



# import yaml
# from whisper_online import FasterWhisperASR, VACOnlineASRProcessor

# class SpeechRecognizer:
#     def __init__(self, config_path: str = "config.yaml"):
#         # 設定読み込み
#         with open(config_path, "r", encoding="utf-8") as f:
#             cfg = yaml.safe_load(f)

#         self.cfg = cfg

#         # ASRモデル初期化
#         self.asr = FasterWhisperASR(
#             lan=cfg["asr"]["language"],
#             modelsize=cfg["asr"]["model"],
#             device=cfg["asr"]["device"]
#         )
#         self.asr.use_vad()

#         # VAD付きオンラインASR
#         self.online = VACOnlineASRProcessor(
#             online_chunk_size=cfg["vad"]["chunk_size"],
#             asr=self.asr,
#             tokenizer=None,
#             buffer_trimming=tuple(cfg["vad"]["buffer_trimming"]),
#             min_silence_duration_ms=cfg["vad"]["silence_ms"]
#         )

#     def insert_audio(self, audio_chunk):
#         """音声チャンクを追加"""
#         self.online.insert_audio_chunk(audio_chunk)

#     def get_result(self):
#         """結果を取得 (逐次 or 確定)"""
#         return self.online.process_iter()

#     def is_final(self):
#         """最後の結果が確定かどうか"""
#         return self.online.is_currently_final

#     def finish(self):
#         """最終処理 (接続終了時に呼ぶ)"""
#         return self.online.finish()

