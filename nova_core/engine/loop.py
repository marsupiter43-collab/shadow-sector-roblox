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
from nova_core.audio.tts import TTSEngine

logger = logging.getLogger(__name__)

class AgentLoop:
    def __init__(self):
        self.state = StateManager()
        self.identity = Identity()
        self.memory = ShortTermMemory()
        self.llm = LLMClient()
        self.dispatcher = EventDispatcher()
        self.tts = TTSEngine()
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
        prompt = text

        logger.debug("Generating response stream...")

        full_response = ""
        current_sentence = ""

        # Sentence ending characters
        sentence_endings = {'.', '!', '?'}

        # We need to buffer characters to properly parse thoughts
        chunk_buffer = ""

        # For tracking state in parsing
        in_thought = False
        thought_buffer = ""

        async for chunk in self.llm.generate_response_stream(sys_prompt, prompt):
            chunk_buffer += chunk

            while True:
                if not in_thought:
                    start_idx = chunk_buffer.find("<thought>")
                    if start_idx != -1:
                        # Found start of thought
                        # Text before <thought> is visible
                        visible_text = chunk_buffer[:start_idx]
                        if visible_text:
                            current_sentence += visible_text

                        chunk_buffer = chunk_buffer[start_idx + len("<thought>"):]
                        in_thought = True
                    else:
                        # Check for partial start tag
                        partial_match = False
                        for i in range(1, len("<thought>")):
                            if chunk_buffer.endswith("<thought>"[:i]):
                                partial_match = True
                                # Text before the partial match is visible
                                visible_text = chunk_buffer[:-i]
                                if visible_text:
                                    current_sentence += visible_text
                                chunk_buffer = chunk_buffer[-i:]
                                break

                        if not partial_match:
                            current_sentence += chunk_buffer
                            chunk_buffer = ""
                        break # Need more chunks

                if in_thought:
                    end_idx = chunk_buffer.find("</thought>")
                    if end_idx != -1:
                        # Found end of thought
                        thought_buffer += chunk_buffer[:end_idx]
                        logger.info(f"[THOUGHT] {thought_buffer.strip()}")
                        thought_buffer = ""
                        chunk_buffer = chunk_buffer[end_idx + len("</thought>"):]
                        in_thought = False
                    else:
                        # Check for partial end tag
                        partial_match = False
                        for i in range(1, len("</thought>")):
                            if chunk_buffer.endswith("</thought>"[:i]):
                                partial_match = True
                                thought_buffer += chunk_buffer[:-i]
                                chunk_buffer = chunk_buffer[-i:]
                                break

                        if not partial_match:
                            thought_buffer += chunk_buffer
                            chunk_buffer = ""
                        break # Need more chunks

            # Check if we have a full sentence to speak in current_sentence
            # Find the last sentence ending
            last_end = -1
            for i, char in enumerate(current_sentence):
                if char in sentence_endings:
                    last_end = i

            if last_end != -1:
                # We have at least one complete sentence
                sentences_to_speak = current_sentence[:last_end + 1]
                current_sentence = current_sentence[last_end + 1:]

                clean_sentence = sentences_to_speak.strip()
                if clean_sentence:
                    asyncio.create_task(self.tts.speak(clean_sentence))
                    full_response += clean_sentence + " "

        # Flush any remaining text
        if current_sentence and not in_thought:
            clean_sentence = current_sentence.strip()
            if clean_sentence:
                asyncio.create_task(self.tts.speak(clean_sentence))
                full_response += clean_sentence + " "

        # Update logs, memory, display
        # We collected full_response without thoughts
        logger.info(f"[NOVA] {full_response.strip()}")
        if not is_proactive and full_response.strip():
            self.memory.add_interaction("Nova", full_response.strip())
        await self.dispatcher.send_to_display(self.state.mood, full_response.strip())

        # Simple dynamic state update based on interaction
        if not is_proactive:
            self.state.update_energy(-2) # Talking takes energy
        else:
            self.state.update_energy(5) # Spontaneous resting recovery
