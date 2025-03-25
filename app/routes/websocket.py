import logging
import json
import uuid
from collections import defaultdict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from deepgram import DeepgramClient, DeepgramClientOptions, LiveTranscriptionEvents, LiveOptions
from app.services.ai import generate_response, check_relevance
from app.services.pinecone import search_pinecone
from app.services.tts import generate_full_tts_audio
from app.config.settings import DEEPGRAM_API_KEY

router = APIRouter()

config = DeepgramClientOptions(
    options={"keepalive": "true"}
)

# Deepgram client configuration
deepgram = DeepgramClient(DEEPGRAM_API_KEY, config)
dg_connection = deepgram.listen.asyncwebsocket.v("1")

# Live transcription options with VAD and auto-endpointing
options = LiveOptions(
    model='nova-2',
    punctuate=True,
    interim_results=True,
    language='en-US',
    smart_format=True,
    utterance_end_ms="1000",  # Marks end of utterance after 1s of silence
    vad_events=True,  # Enables voice activity detection
    endpointing=2000   # Stops transcribing after 2s of silence
)

# Dictionary to store transcription buffers for each client
transcription_buffers = defaultdict(list)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Assign a unique ID to each client
    socket_id = str(uuid.uuid4())

    try:
        await websocket.accept()
        logging.info(f"📡 Client connected: {socket_id}")

        await dg_connection.start(options)
        logging.info(f"Deepgram WebSocket started for {socket_id}")

        async def on_message(self, result, **kwargs):
            sentence = result.channel.alternatives[0].transcript.strip()
            if not sentence:
                return  

            # logging.info(f"Partial Transcription [{socket_id}]: {sentence}")

            # Append to this client's buffer
            transcription_buffers[socket_id].append(sentence)

            logging.info(f"Transcription Buffers [{socket_id}]: {transcription_buffers[socket_id]}")

            # If Deepgram detects speech has ended
            if getattr(result.channel.alternatives[0], "is_final", True) or getattr(result.channel.alternatives[0], "speech_final", True):
                final_transcription = " ".join(transcription_buffers[socket_id])

                if final_transcription:  # Avoid sending empty transcriptions
                    logging.info(f"📝 Final Transcription [{socket_id}]: {final_transcription}")

                    await websocket.send_text(json.dumps({
                        "socket_id": socket_id,
                        "type": "transcription",
                        "text": final_transcription
                    }))

                    transcription_buffers[socket_id] = []  # ✅ Clear only after processing

                    ai_response = await process_transcription(final_transcription)
                    logging.info(f"🤖 AI Response [{socket_id}]: {ai_response}")

                    await websocket.send_text(json.dumps({
                        "socket_id": socket_id,
                        "type": "ai_response",
                        "text": ai_response
                    }))

                    if ai_response:
                        await generate_full_tts_audio(ai_response, websocket)


        async def on_error(self, error, **kwargs):
            logging.error(f"Error [{socket_id}]: {error}")

        if not hasattr(dg_connection, "_event_attached"):
            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            dg_connection.on(LiveTranscriptionEvents.Error, on_error)
            dg_connection._event_attached = True
            

        while True:
            try:
                audio_data = await websocket.receive_bytes()
                await dg_connection.send(audio_data)

            except WebSocketDisconnect:
                logging.info(f"🔌 Client disconnected: {socket_id}")
                # transcription_buffers.pop(socket_id, None)  # Clean up buffer
                await dg_connection.finish()
                break
            except Exception as e:
                logging.error(f"❌ Error receiving audio [{socket_id}]: {e}")

    except Exception as e:
        logging.error(f"Failed to start WebSocket for {socket_id}: {e}")

async def process_transcription(transcription: str):
    retrieved_context = search_pinecone(transcription)
    is_relevant = check_relevance(transcription, retrieved_context) if retrieved_context else False
    context_prompt = retrieved_context if is_relevant else None
    return generate_response(transcription, context_prompt)