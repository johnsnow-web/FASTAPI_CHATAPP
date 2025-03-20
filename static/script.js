document.addEventListener("DOMContentLoaded", function () {
    const chatBox = document.getElementById("chat-box");
    const startSpeaking = document.getElementById("startSpeaking");
    const endSpeaking = document.getElementById("endSpeaking");

    let ws;
    let mediaRecorder;
    let audioStream;
    let isTranscriptionStarted = false;

    function connectWebSocket() {
        if (!ws || ws.readyState === WebSocket.CLOSED) {
            ws = new WebSocket("ws://127.0.0.1:8000/ws");

            ws.onopen = () => console.log("✅ WebSocket Connected");

            ws.binaryType = 'arraybuffer';

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

    async function startRecording() {
        if (isTranscriptionStarted) {
            console.log("Cannot start recording while AI is responding.");
            return;
        }

        try {
            audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            console.log("🎤 Microphone access granted.");

            mediaRecorder = new MediaRecorder(audioStream, { mimeType: "audio/webm" });
            mediaRecorder.start(100); 

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0 && ws.readyState === WebSocket.OPEN) {
                    event.data.arrayBuffer().then((buffer) => {
                        const uint8Array = new Uint8Array(buffer);
                        ws.send(uint8Array);
                    });
                }
            };

            console.log("🔴 Recording started...");
        } catch (error) {
            console.error("❌ Microphone access denied:", error);
        }
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state !== "inactive") {
            mediaRecorder.stop();
            console.log("⏹️ Stopping recording...");
        }
        if (audioStream) {
            audioStream.getTracks().forEach((track) => track.stop());
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
 
 
     startSpeaking.addEventListener("click", startRecording);
     endSpeaking.addEventListener("click", stopRecording);
 });