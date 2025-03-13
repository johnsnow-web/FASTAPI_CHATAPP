import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
import logging

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize FastAPI app
app = FastAPI()
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize memory for conversation history
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Initialize AI model
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", google_api_key=GEMINI_API_KEY)

@app.get("/")
async def root():
    return {"message": "Server is running. Go to /static/index.html"}

# WebSocket route for real-time chat
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logging.info("Client connected.")

    try:
        while True:
            data = await websocket.receive_text()
            logging.info(f"Received message: {data}")

            # Retrieve past conversation history
            past_conversation = "\n".join(
                [f"User: {msg.content}" if i % 2 == 0 else f"AI: {msg.content}"
                 for i, msg in enumerate(memory.chat_memory.messages)]
            )

            # AI prompt
            prompt = f"""
                You are an AI assistant. Provide a structured response:
                - Keep it concise.
                - Use bullet points if needed.
                - Maintain clarity.

                Previous conversation:\n{past_conversation}

                User: {data}
                AI:
            """

            # Get AI response
            response = llm.invoke(prompt)
            ai_reply = response.content if hasattr(response, "content") else str(response)

            # Store in memory
            memory.save_context({"input": data}, {"output": ai_reply})

            # Send response
            await websocket.send_text(ai_reply)
            logging.info(f"Sent AI response: {ai_reply}")

    except WebSocketDisconnect:
        logging.info("Client disconnected.")
    except Exception as e:
        logging.error(f"Error processing message: {e}")
