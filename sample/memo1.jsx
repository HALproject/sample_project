useEffect(() => {
  const ws = new WebSocket("ws://localhost:8000/ws/audio");
  wsRef.current = ws;

  ws.onopen = () => {
    // 最初に設定を送信
    ws.send(
      JSON.stringify({
        model: "small",   // "small" or "finetuned"
        vad: true         // true = VAD ON, false = OFF
      })
    );
  };

  ws.onmessage = (event) => {
    setMessages((prev) => [...prev, event.data]);
  };

  navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
    const mediaRecorder = new MediaRecorder(stream, {
      mimeType: "audio/webm;codecs=pcm",
    });

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0 && ws.readyState === WebSocket.OPEN) {
        e.data.arrayBuffer().then((buf) => {
          ws.send(buf);
        });
      }
    };

    mediaRecorder.start(200); // 200msごとに送信
  });

  return () => {
    ws.close();
  };
}, []);