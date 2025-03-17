import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.ai import generate_response, check_relevance
from app.services.pinecone import search_pinecone
from app.services.memory import save_chat_history

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logging.info("📡 Client connected.")

    try:
        while True:
            user_query = await websocket.receive_text()
            logging.info(f"📩 Received query: {user_query}")

            # Step 1: Search Pinecone
            retrieved_context = search_pinecone(user_query)

            # Step 2: Check relevance
            is_relevant = check_relevance(user_query, retrieved_context) if retrieved_context else False

            # Step 3: Select data source
            context_prompt = retrieved_context if is_relevant else None

            # Step 4: Generate AI response
            ai_reply = generate_response(user_query, context_prompt)


            # Step 5: Save chat history
            save_chat_history(user_query, ai_reply)

            # Step 6: Send response
            await websocket.send_text(ai_reply)
            logging.info(f"📤 Sent AI response: {ai_reply}")

    except WebSocketDisconnect:
        logging.info("🔌 Client disconnected.")
    except Exception as e:
        logging.error(f"❌ Error processing message: {e}")
