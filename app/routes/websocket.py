import logging
import asyncio
import time
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from app.services.ai import generate_response, check_relevance
# from app.services.memory import get_chat_history
from app.services.pinecone import search_pinecone
from app.services.tts import generate_full_tts_audio
from app.config.settings import DEEPGRAM_API_KEY

router = APIRouter()

# Deepgram client configuration
deepgram = DeepgramClient(DEEPGRAM_API_KEY)
dg_connection = deepgram.listen.asyncwebsocket.v("1")

options = LiveOptions(
    model='nova-3',
    punctuate=True,
    interim_results=False,
    language='en-Us',
    smart_format=True
)

transcription_buffer = []
last_speech_time = None
silence_task = None

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global transcription_buffer, last_speech_time, silence_task
    try:
        await websocket.accept()
        logging.info("📡 Client connected.")

        await dg_connection.start(options)
        logging.info("Deepgram WebSocket connection started.")

        async def on_message(self, result, **kwargs):
            global transcription_buffer, last_speech_time, silence_task

            sentence = result.channel.alternatives[0].transcript.strip()
            if not sentence:
                return  

            logging.info(f"Partial Transcription: {sentence}")

            last_speech_time = time.time()
            transcription_buffer.append((sentence, last_speech_time))

            # Remove speech older than 3 seconds
            transcription_buffer = [(s, t) for s, t in transcription_buffer if time.time() - t <= 3]

            final_text = " ".join([s for s, t in transcription_buffer])
            
            if silence_task:
                silence_task.cancel()
            silence_task = asyncio.create_task(silence_detected(websocket))

        async def on_error(self, error, **kwargs):
            logging.error(f"Error: {error}")

        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)

        while True:
            try:
                audio_data = await websocket.receive_bytes()
                await dg_connection.send(audio_data) 

            except WebSocketDisconnect:
                logging.info("🔌 Client disconnected.")
                await dg_connection.finish()
                break
            except Exception as e:
                logging.error(f"❌ Error receiving audio: {e}")

    except Exception as e:
        logging.error(f"Failed to start Deepgram WebSocket connection: {e}")

async def silence_detected(websocket):
    global transcription_buffer

    await asyncio.sleep(1.5)  # Wait 1.5 seconds to confirm silence

    if transcription_buffer:
        final_transcription = " ".join([s for s, t in transcription_buffer])
        transcription_buffer = []  

        logging.info(f"⏳ Silence detected. Sending final transcription: {final_transcription}")

        await websocket.send_text(json.dumps({"type": "transcription", "text": final_transcription}))

        # Delay before sending to AI to ensure frontend updates first
        # await asyncio.sleep(0.1)  

        ai_response = await process_transcription(final_transcription)
        logging.info(f"🤖 AI Response: {ai_response}")
        await websocket.send_text(json.dumps({"type": "ai_response", "text": ai_response}))
        if ai_response:
            await generate_full_tts_audio(ai_response, websocket)

async def process_transcription(transcription: str):
    # chat_history = get_chat_history()
    retrieved_context = search_pinecone(transcription)
    is_relevant = check_relevance(transcription, retrieved_context) if retrieved_context else False
    context_prompt = retrieved_context if is_relevant else None
    return generate_response(transcription, context_prompt)