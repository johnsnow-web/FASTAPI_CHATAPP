document.addEventListener("DOMContentLoaded", function () {
    const chatBox = document.getElementById("chat-box");
    const messageInput = document.getElementById("message");
    const sendBtn = document.getElementById("sendBtn");

    let ws;
    let audioContext = new (window.AudioContext || window.webkitAudioContext)();
    let source;

    function connectWebSocket() {
        if (!ws || ws.readyState === WebSocket.CLOSED) {
            ws = new WebSocket("ws://127.0.0.1:8000/ws");

            ws.onopen = () => console.log("✅ WebSocket Connected");

            ws.onmessage = async (event) => {
                console.log("📩 Received:", event.data);

                if (event.data instanceof Blob) {
                    console.log("📦 Audio chunk received:", event.data);
                    playAudioStream(event.data);
                } else if (typeof event.data === "string") {
                    console.log("📩 Text received:", event.data);
                    addMessage(event.data); // Correctly pass string
                } else {
                    console.error("Received unexpected data type:", typeof event.data);
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

    sendBtn.addEventListener("click", () => {
        const message = messageInput.value.trim();
        if (message) {
            addMessage("You", message);
            messageInput.value = "";

            if (ws.readyState === WebSocket.OPEN) {
                ws.send(message);
            } else {
                console.error("WebSocket Closed ❌ Reconnecting...");
                connectWebSocket();
                setTimeout(() => {
                    if (ws.readyState === WebSocket.OPEN) {
                        ws.send(message);
                    }
                }, 1000);
            }
        }
    });

    function addMessage(user, text) {
        let msgDiv = document.createElement("div");
        msgDiv.classList.add("message");
        msgDiv.innerHTML = `<strong>${user}:</strong> ${text}`;
        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    async function playAudioStream(audioBlob) {
        try {
            const arrayBuffer = await audioBlob.arrayBuffer();
            console.log("Audio ArrayBuffer:", arrayBuffer);
            const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

            if (source) source.stop();

            source = audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(audioContext.destination);
            source.start(0);

            console.log("🎶 Playing audio chunk...");
        } catch (error) {
            console.error("Error playing audio:", error);
        }
    }
});
