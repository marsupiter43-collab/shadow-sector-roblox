import asyncio
import logging
import queue
import threading
import time

import numpy as np
import sounddevice as sd
import webrtcvad
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)


class STTEngine:
    def __init__(self, callback_queue: asyncio.Queue):
        self.callback_queue = callback_queue
        self.device = "cuda"
        self.compute_type = "int8"
        self.model_size = "small"
        self.language = "ru"

        # Audio capturing parameters
        self.sample_rate = 16000
        self.frame_duration_ms = 30  # 30 ms frames for VAD
        self.frame_size = int(self.sample_rate * (self.frame_duration_ms / 1000.0))

        self.vad = webrtcvad.Vad(3) # Aggressiveness 3 (most aggressive)

        self.running = False
        self.model = None

        self.capture_thread = None
        self.process_thread = None

        # Thread-safe queue to pass audio chunks to transcription thread
        self.audio_queue = queue.Queue()
        self.main_loop = None

    def load_model(self):
        logger.info("Loading STT model (faster-whisper)...")
        try:
            self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
            logger.info("STT model loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading STT model: {e}")

    def start(self):
        self.running = True

        # Capture the current asyncio loop from the main thread
        try:
            self.main_loop = asyncio.get_running_loop()
        except RuntimeError:
            self.main_loop = asyncio.get_event_loop()

        self.process_thread = threading.Thread(target=self._transcribe_loop, daemon=True)
        self.process_thread.start()

        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        logger.info("STT listening started.")

    def stop(self):
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)

        # Push sentinel to process queue
        self.audio_queue.put(None)
        if self.process_thread:
            self.process_thread.join(timeout=2.0)
        logger.info("STT listening stopped.")

    def _capture_loop(self):
        """Continuously captures audio from mic, uses VAD to chunk speech."""
        speech_buffer = []
        is_speaking = False
        silence_frames = 0
        max_silence_frames = int(1.5 / (self.frame_duration_ms / 1000.0)) # 1.5 seconds silence to split

        # Use a thread-safe queue to pass frames from callback to processing loop
        frame_queue = queue.Queue()

        def callback(indata, frames, time_info, status):
            if status:
                logger.warning(f"SoundDevice status: {status}")
            if not self.running:
                raise sd.CallbackStop()

            # Put bytes into the thread-safe queue
            frame_queue.put(indata.tobytes())

        try:
            with sd.RawInputStream(samplerate=self.sample_rate, blocksize=self.frame_size, dtype='int16', channels=1, callback=callback):
                buffer = bytearray()
                bytes_per_frame = self.frame_size * 2 # 16-bit PCM = 2 bytes per sample

                while self.running:
                    # Drain the queue into our local buffer
                    while not frame_queue.empty():
                        try:
                            buffer.extend(frame_queue.get_nowait())
                        except queue.Empty:
                            break

                    # Process buffer in VAD frame sizes
                    while len(buffer) >= bytes_per_frame:
                        frame_bytes = bytes(buffer[:bytes_per_frame])
                        del buffer[:bytes_per_frame]

                        is_speech = self.vad.is_speech(frame_bytes, self.sample_rate)

                        if is_speech:
                            if not is_speaking:
                                is_speaking = True
                            silence_frames = 0
                            speech_buffer.append(frame_bytes)
                        else:
                            if is_speaking:
                                silence_frames += 1
                                speech_buffer.append(frame_bytes)

                                if silence_frames >= max_silence_frames:
                                    # End of speech segment
                                    is_speaking = False

                                    # Send to processing queue
                                    audio_data = b''.join(speech_buffer)
                                    self.audio_queue.put(audio_data)

                                    speech_buffer = []
                                    silence_frames = 0

                    time.sleep(0.01)
        except Exception as e:
            logger.error(f"Error in STT capture loop: {e}")

    def _transcribe_loop(self):
        """Processes chunks from the queue and transcribes them using faster-whisper."""
        self.load_model()

        while self.running:
            try:
                audio_bytes = self.audio_queue.get(timeout=1.0)
                if audio_bytes is None:
                    break

                if not self.model:
                    continue

                # Convert bytes to numpy float32 array normalized -1.0 to 1.0 for whisper
                audio_np = np.frombuffer(audio_bytes, np.int16).astype(np.float32) / 32768.0

                # Minimum duration check (e.g. 0.5 seconds)
                if len(audio_np) < self.sample_rate * 0.5:
                    continue

                segments, info = self.model.transcribe(audio_np, language=self.language, beam_size=5)

                text = ""
                for segment in segments:
                    text += segment.text + " "

                text = text.strip()
                if text:
                    logger.info(f"[HEARD] {text}")
                    # Push to async queue safely from thread
                    if self.main_loop and self.main_loop.is_running():
                        asyncio.run_coroutine_threadsafe(self.callback_queue.put(text), self.main_loop)

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error transcribing audio: {e}")
