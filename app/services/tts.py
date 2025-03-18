import logging
import asyncio
import httpx
from app.config.settings import DEEPGRAM_API_KEY

DEEPGRAM_TTS_URL = "https://api.deepgram.com/v1/speak"


async def generate_full_tts_audio(text):
    """
    Generates full speech audio from Deepgram TTS API and returns binary data.
    """
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"text": text} 

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