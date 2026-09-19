import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class EventDispatcher:
    """
    Stub dispatcher for routing output events to physical or network interfaces.
    """

    def __init__(self):
        pass

    async def send_to_display(self, emotion: str, text: str) -> None:
        """
        Send text and an emotion state to the display (e.g. WebSocket, Serial).
        """
        logger.info(f"[DISPLAY] Emotion: {emotion} | Text: {text}")

    async def send_to_actuator(self, command: Dict[str, Any]) -> None:
        """
        Send physical commands to hardware actuators.
        """
        logger.info(f"[ACTUATOR] Command: {command}")
