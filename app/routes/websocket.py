import logging
import asyncio
import httpx
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.ai import generate_response, check_relevance
from app.services.pinecone import search_pinecone
from app.config.settings import DEEPGRAM_API_KEY
from app.services.memory import get_chat_history  # Import the function to get chat history

router = APIRouter()

DEEPGRAM_TTS_URL = "https://api.deepgram.com/v1/speak"

async def generate_full_tts_audio(text):
    """
    Generates full speech audio from Deepgram TTS API and returns binary data.
    """
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"text": text}  # Ensure only `text` is sent

    async with httpx.AsyncClient() as client:
        response = await client.post(DEEPGRAM_TTS_URL, headers=headers, json=payload)

        if response.status_code != 200:
            logging.error(f"❌ Deepgram TTS API Error: {response.text}")
            return None
        
        audio_data = response.content  # Get binary audio response
        if not audio_data:
            logging.error("❌ Deepgram did not return audio data.")
            return None

        return audio_data  # Return full audio data

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logging.info("📡 Client connected.")

    try:
        while True:
            try:
                user_query = await websocket.receive_text()
            except WebSocketDisconnect:
                logging.info("🔌 Client disconnected.")
                break
            except Exception as e:
                logging.error(f"❌ Error receiving message: {e}")
                continue

            user_query = user_query.strip()
            if not user_query:
                logging.warning("⚠️ Empty message received, ignoring.")
                continue

            logging.info(f"📩 Received query: {user_query}")

            # Step 1: Fetch chat history
            chat_history = get_chat_history()  # Get the chat history

            # Step 2: Search Pinecone
            retrieved_context = search_pinecone(user_query)

            # Step 3: Check relevance
            is_relevant = check_relevance(user_query, retrieved_context) if retrieved_context else False

            # Step 4: Select data source
            context_prompt = retrieved_context if is_relevant else None

            # Step 5: Generate AI response (Text)
            ai_reply = generate_response(user_query, context_prompt=retrieved_context, chat_history=chat_history)  # Pass chat history
            logging.info(f"🎙️ AI Response: {ai_reply}")

            # Send AI response text first
            await websocket.send_text(ai_reply)

            # Step 6: Generate full TTS audio
            audio_data = await generate_full_tts_audio(ai_reply)
            if audio_data:
                await websocket.send_bytes(audio_data)  # Send full audio after generation
                logging.info("✅ Sent full audio to frontend.")

    except Exception as e:
        logging.error(f"❌ Unexpected error in WebSocket: {e}")
    finally:
        await websocket.close()
        logging.info("✅ WebSocket closed cleanly.")
