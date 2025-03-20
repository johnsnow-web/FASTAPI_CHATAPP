import asyncio
import json
from app.config.settings import DEEPGRAM_API_KEY
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from deepgram import DeepgramClient, DeepgramClientOptions, SpeakWebSocketEvents, SpeakWSOptions




# Initialize Deepgram client
config = DeepgramClientOptions(options={"speaker_playback": "true"})
deepgram = DeepgramClient(DEEPGRAM_API_KEY, config)


async def generate_full_tts_audio(text: str, websocket: WebSocket):
    try:
        print("🔍 Checking Deepgram...")
        dg_connection = deepgram.speak.asyncwebsocket.v("1")
        
        async def on_binary_data(self, data, **kwargs):
            await websocket.send_bytes(data)

        dg_connection.on(SpeakWebSocketEvents.AudioData, on_binary_data)

        options = SpeakWSOptions(
            model="aura-asteria-en",
            encoding="linear16",
            sample_rate=16000,
        )

        if not await dg_connection.start(options):
            print("❌ Failed to start Deepgram connection")
            return

        print("✅ Sending text to Deepgram TTS")
        await dg_connection.send_text(text)
        await dg_connection.flush()
        await dg_connection.wait_for_complete()
        await dg_connection.finish()
        
    except ModuleNotFoundError as e:
        print(f"🚨 Missing module error: {e}")
    except Exception as e:
        print(f"❌ Error in TTS generation: {e}")
