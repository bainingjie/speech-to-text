document.addEventListener("DOMContentLoaded", function () {
  const webSocket = new WebSocket("ws://localhost:8765");

  webSocket.onopen = function () {
    console.log("WebSocket connection opened");
  };

  webSocket.onmessage = function (event) {
    console.log("WebSocket message received:", event.data);
    displayMessage(event.data);

    // 受信したメッセージを読み上げる
    const message = event.data;
    const speech = new SpeechSynthesisUtterance(message);
    speech.lang = "en-US"; // 英語に設定

    // 音声合成エンジンの availability をチェック
    if (window.speechSynthesis.getVoices().length > 0) {
      window.speechSynthesis.speak(speech);
    } else {
      console.warn("No speech synthesis voices available");
    }
  };

  webSocket.onclose = function () {
    console.log("WebSocket connection closed");
  };

  webSocket.onerror = function (event) {
    console.error("WebSocket error:", event);
  };

  function displayMessage(message) {
    const el = document.querySelector("#message");
    el.textContent = message;
  }

  // 音声合成エンジンの availability をチェック
  window.speechSynthesis.onvoiceschanged = function () {
    if (window.speechSynthesis.getVoices().length > 0) {
      console.log("Speech synthesis voices available");
    } else {
      console.warn("No speech synthesis voices available");
    }
  };
});