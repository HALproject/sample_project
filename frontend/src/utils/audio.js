// src/utils/audio.js
// Base64 WAV再生
export function playBase64Wav(base64) {
  if (!base64) return;
  const byteString = atob(base64);
  const len = byteString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) bytes[i] = byteString.charCodeAt(i);
  const blob = new Blob([bytes.buffer], { type: "audio/wav" });
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);
  audio.onended = () => URL.revokeObjectURL(url);
  audio.play().catch(() => {/* autoplay対策で失敗する場合あり */});
}
