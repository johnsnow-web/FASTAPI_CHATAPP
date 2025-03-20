import logging
import asyncio
import httpx
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.config.settings import DEEPGRAM_API_KEY
from app.services.pinecone import search_pinecone
from app.services.ai import generate_response, check_relevance
from app.services.tts import generate_full_tts_audio

router = APIRouter()

# # Enable CORS for frontend access
# router.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

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

 

            # Step 2: Search Pinecone
            retrieved_context = search_pinecone(user_query)

            # Step 3: Check relevance
            is_relevant = check_relevance(user_query, retrieved_context) if retrieved_context else False

            # Step 4: Select data source
            context_prompt = retrieved_context if is_relevant else None

            # Step 5: Generate AI response (Text)
            ai_response = generate_response(user_query, context_prompt=retrieved_context)


            if ai_response:
                await generate_full_tts_audio(ai_response, websocket)  
                logging.info("✅ Sent full audio to frontend.")

    except Exception as e:
        logging.error(f"❌ Unexpected error in WebSocket: {e}")
    finally:
        await websocket.close()
        logging.info("✅ WebSocket closed cleanly.")
