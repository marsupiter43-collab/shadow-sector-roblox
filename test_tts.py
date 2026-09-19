import asyncio
from nova_core.audio.tts import TTSEngine

async def test():
    e = TTSEngine()
    await e.speak("Привет!")

asyncio.run(test())
