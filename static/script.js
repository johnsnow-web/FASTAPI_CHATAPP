document.addEventListener("DOMContentLoaded", function () {
    const chatBox = document.getElementById("chat-box");
    const messageInput = document.getElementById("message");
    const startSpeaking = document.getElementById("startSpeaking");
    const endSpeaking = document.getElementById("endSpeaking");

    let ws;
    let recognition;
    let silenceTimer;
    let transcriptBuffer = "";

    function connectWebSocket() {
        if (!ws || ws.readyState === WebSocket.CLOSED) {
            ws = new WebSocket("ws://127.0.0.1:8000/ws");

            ws.onopen = () => console.log("✅ WebSocket Connected");

            ws.onmessage = async (event) => {
                if (typeof event.data === "string") {
                    addMessage("AI", event.data); 
                } else if (event.data instanceof Blob) {
                    const arrayBuffer = await event.data.arrayBuffer();
                    playAudioStream(arrayBuffer);
                }
            };
            ws.onclose = () => {
                console.warn("❌ WebSocket Disconnected. Reconnecting...");
                setTimeout(connectWebSocket, 2000);
            };

            ws.onerror = (error) => console.error("❌ WebSocket Error:", error);
        }
    }

    connectWebSocket();

    function startSpeechRecognition() {
        if (!("webkitSpeechRecognition" in window)) {
            alert("Your browser does not support speech recognition.");
            return;
        }

        recognition = new webkitSpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = "en-US";

        recognition.onstart = () => console.log("🎙️ Speech recognition started...");
        recognition.onerror = (event) => console.error("Speech recognition error:", event.error);

        recognition.onresult = (event) => {
            let finalText = "";
            for (let i = event.resultIndex; i < event.results.length; i++) {
                let transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalText += transcript + " ";
                }
            }

            if (finalText.trim()) {
                transcriptBuffer = finalText.trim();
                addMessage("You", transcriptBuffer);
            }

            resetSilenceTimer();
        };

        recognition.start();
    }

    function resetSilenceTimer() {
        if (silenceTimer) clearTimeout(silenceTimer);
        silenceTimer = setTimeout(() => {
            if (transcriptBuffer.trim()) {
                sendToBackend(transcriptBuffer);
                transcriptBuffer = ""; 
            }
        }, 1000);
    }

    function sendToBackend(text) {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(text);
        } else {
            console.error("WebSocket Closed ❌ Reconnecting...");
            connectWebSocket();
            setTimeout(() => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send(text);
                }
            }, 1000);
        }
    }

    function addMessage(user, text) {
        let msgDiv = document.createElement("div");
        msgDiv.classList.add("message");
        msgDiv.innerHTML = `<strong>${user}:</strong> ${text}`;
        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Create a single AudioContext
    let audioContext = new (window.AudioContext || window.webkitAudioContext)();

    function playAudioStream(audioBlob) {
        audioBlob.arrayBuffer()
            .then((arrayBuffer) => audioContext.decodeAudioData(arrayBuffer))
            .then((audioBuffer) => {
                let source = audioContext.createBufferSource();
                source.buffer = audioBuffer;
                source.connect(audioContext.destination);
                source.start();
            })
            .catch((error) => console.error("Error decoding audio data:", error));
    }


    startSpeaking.addEventListener("click", startSpeechRecognition);
    endSpeaking.addEventListener("click", () => recognition && recognition.stop());
});