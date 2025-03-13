document.addEventListener("DOMContentLoaded", function () {
    const chatBox = document.getElementById("chat-box");
    const messageInput = document.getElementById("message");
    const sendBtn = document.getElementById("sendBtn");
    const startSpeakingBtn = document.getElementById("startSpeaking");
    const endSpeakingBtn = document.getElementById("endSpeaking");

    let recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    let ws;

    function connectWebSocket() {
        if (!ws || ws.readyState === WebSocket.CLOSED) {
            ws = new WebSocket("ws://127.0.0.1:8000/ws");

            ws.onopen = () => console.log("WebSocket Connected ✅");
            ws.onmessage = (event) => addMessage("AI", event.data);
            ws.onclose = () => console.log("WebSocket Disconnected ❌");
            ws.onerror = (error) => console.error("WebSocket Error:", error);
        }
    }

    connectWebSocket();

    startSpeakingBtn.addEventListener("click", () => {
        recognition.start();
        startSpeakingBtn.style.background = "darkgreen";
    });

    endSpeakingBtn.addEventListener("click", () => {
        recognition.stop();
        startSpeakingBtn.style.background = "green";
    });

    recognition.onresult = (event) => {
        messageInput.value = event.results[0][0].transcript;
    };

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
    
        // Properly format bullet points, bold text, and newlines
        let formattedText = text
            .replace(/\n/g, "<br>") // Convert newlines to <br>
            .replace(/\*{2}(.*?)\*{2}/g, "<strong>$1</strong>") // Bold text (**text** → <strong>text</strong>)
            .replace(/\* (.*?)(<br>|$)/g, "<li>$1</li>"); // Convert bullet points (* text) into <li>
    
        // Wrap bullet points inside <ul> if they exist
        if (formattedText.includes("<li>")) {
            formattedText = "<ul>" + formattedText + "</ul>";
        }
    
        msgDiv.innerHTML = `<strong>${user}:</strong> ${formattedText}`;
        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }
    
});