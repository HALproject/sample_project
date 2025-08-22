// 設定変更リクエストを送る
ws.send(
  JSON.stringify({
    command: "update_config",
    model: "finetuned",
    temperature: 0.7,
    vad: false,
  })
);