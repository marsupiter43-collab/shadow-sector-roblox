import httpx
import logging
from typing import Dict, Any, List

from nova_core.config.settings import settings

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, base_url: str = settings.ollama_url, model: str = settings.model_name):
        self.base_url = base_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=60.0)

    async def generate_response(self, system_prompt: str, prompt: str) -> str:
        """
        Calls Ollama's /api/generate asynchronously.
        """
        payload = {
            "model": self.model,
            "system": system_prompt,
            "prompt": prompt,
            "stream": False
        }

        url = f"{self.base_url}/api/generate"

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return f"<thought>I failed to contact my language model: {e}</thought> An internal error occurred."

    async def close(self):
        await self.client.aclose()
