import asyncio
import logging
from typing import Optional

from nova_core.config.settings import settings
from nova_core.engine.state_manager import StateManager
from nova_core.engine.identity import Identity
from nova_core.memory.short_term import ShortTermMemory
from nova_core.llm.client import LLMClient
from nova_core.llm.parser import parse_llm_response
from nova_core.comms.dispatcher import EventDispatcher

logger = logging.getLogger(__name__)

class AgentLoop:
    def __init__(self):
        self.state = StateManager()
        self.identity = Identity()
        self.memory = ShortTermMemory()
        self.llm = LLMClient()
        self.dispatcher = EventDispatcher()
        self.input_queue: asyncio.Queue[str] = asyncio.Queue()

        self.running = False
        self.idle_task: Optional[asyncio.Task] = None

    async def start(self):
        self.running = True
        self.idle_task = asyncio.create_task(self._idle_ticker())

        logger.info("Agent loop started.")

        while self.running:
            try:
                # Wait for user input
                user_input = await self.input_queue.get()

                if user_input is None:
                    # Sentinel value to shut down
                    self.input_queue.task_done()
                    break

                # Reset idle state
                self.state.reset_idle()

                # Process input
                await self.process_stimulus(user_input, is_proactive=False)

                self.input_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")

    async def stop(self):
        self.running = False
        # Push a sentinel to unblock the input queue
        await self.input_queue.put(None)
        if self.idle_task:
            self.idle_task.cancel()
        await self.llm.close()
        logger.info("Agent loop stopped.")

    async def _idle_ticker(self):
        """Periodically increments idle timer and triggers proactive behavior if needed."""
        try:
            while self.running:
                await asyncio.sleep(settings.idle_tick_seconds)
                self.state.tick_idle(settings.idle_tick_seconds)
                logger.debug(f"Tick: Idle for {self.state.idle_seconds}s")

                if self.state.idle_seconds >= settings.proactive_trigger_seconds:
                    logger.info("Proactive trigger reached.")
                    self.state.reset_idle()
                    # Trigger proactive thought
                    await self.process_stimulus("Generate a spontaneous thought based on your current state.", is_proactive=True)
        except asyncio.CancelledError:
            pass

    async def process_stimulus(self, text: str, is_proactive: bool = False):
        """Processes input or proactive trigger, calls LLM, and handles output."""
        if not is_proactive:
            logger.info(f"User: {text}")
            self.memory.add_interaction("User", text)

        sys_prompt = self.identity.generate_system_prompt(self.state, self.memory)

        # Determine prompt sent to LLM
        if is_proactive:
            prompt = text
        else:
            prompt = text

        logger.debug("Generating response...")
        raw_response = await self.llm.generate_response(sys_prompt, prompt)

        thought, visible = parse_llm_response(raw_response)

        if thought:
            logger.info(f"[THOUGHT] {thought}")

        if visible:
            logger.info(f"[NOVA] {visible}")
            if not is_proactive:
                self.memory.add_interaction("Nova", visible)
            await self.dispatcher.send_to_display(self.state.mood, visible)

        # Simple dynamic state update based on interaction
        if not is_proactive:
            self.state.update_energy(-2) # Talking takes energy
        else:
            self.state.update_energy(5) # Spontaneous resting recovery
