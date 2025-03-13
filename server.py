import os
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# Initialize memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Initialize AI model
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", google_api_key=GEMINI_API_KEY)

@app.get("/")
async def root():
    return {"message": "Server is running. Go to /static/index.html"}

# WebSockets for real-time chat
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            print(f"Incoming message: {data}")  # Log incoming data

            # Retrieve past conversation history
            past_conversation = "\n".join(
                [f"{msg.type}: {msg.content}" for msg in memory.chat_memory.messages]
            )

            # Modify prompt for concise response
            prompt = f"""
                    You are an AI assistant. Provide a structured, point-to-point response.
                    - Keep it concise.
                    - Use bullet points if needed.
                    - Maintain clarity.

                    Previous conversation:\n{past_conversation}

                    User: {data}
                    AI:
                    """

            # AI Response
            response = llm.invoke(prompt)
            memory.save_context({"input": data}, {"output": response.content})
            await websocket.send_text(response.content)

        except Exception as e:
            print(f"Error processing message: {e}")
            break  # Exit the loop on error  