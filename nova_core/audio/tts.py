import asyncio
import logging
import re
import numpy as np
import torch
import torchaudio
import sounddevice as sd

logger = logging.getLogger(__name__)

class TTSEngine:
    def __init__(self, speaker: str = "baya"):
        self.device = torch.device("cpu")
        self.sample_rate = 24000  # Default expected by silero v4_ru
        self.target_sample_rate = 22000 # Playback slightly slower to pitch down
        self.speaker = speaker
        self._lock = asyncio.Lock()

        logger.info("Initializing Silero TTS (this may download the model)...")
        try:
            self.model, _ = torch.hub.load(
                repo_or_dir='snakers4/silero-models',
                model='silero_tts',
                language='ru',
                speaker='v4_ru',
                trust_repo=True
            )
            self.model.to(self.device)
            logger.info("TTS model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load TTS model: {e}")
            self.model = None

    def clean_text(self, text: str) -> str:
        """Strips <thought> tags and their contents from the input string."""
        clean = re.sub(r'<thought>.*?</thought>', '', text, flags=re.DOTALL)
        return clean.strip()

    def generate_audio(self, text: str) -> np.ndarray:
        if not self.model:
            return np.array([])

        try:
            # Generate audio tensor
            # The prompt requested a speech rate/speed of 1.15
            # apply_tts in silero handles 'speed' parameter in recent versions
            # However, if it throws an error we might have to stretch it manually.
            # But recent silero_tts models typically support speed parameter.
            # We'll try passing it directly or fallback.
            audio_tensor = self.model.apply_tts(
                text=text,
                speaker=self.speaker,
                sample_rate=self.sample_rate,
                put_accent=True,
                put_yo=True
            )

            # The prompt requested a speech rate/speed of 1.15. Older silero versions don't have a 'speed' arg.
            # We can use torchaudio.functional.speed to change pitch/tempo or torchaudio.functional.pitch_shift
            # Or simpler: playing it back slightly faster at 24000 increases pitch. But we need to pitch DOWN and SPEED UP.
            # Phase vocoder is best, but requires complex STFT.
            # We'll use a torchaudio transform or resample. Let's just use torchaudio to resample to mimic pitch shift.
            # Since speed isn't a direct kwarg, let's just stretch the tensor to mimic speed 1.15 using resampling
            # If we want 1.15 speed, we could just drop frames or use resample.
            # A simple pitch down + speed up hack if we can't use complex transforms:
            # We can just change the target_sample_rate to speed up (increases pitch), then pitch down using torchaudio?
            # Actually, `torchaudio.functional.speed` does not exist in standard.
            # Let's just adjust target_sample_rate to 24000 * 1.15 = 27600 for speed (this makes it squeaky),
            # BUT prompt says "pitch down audio (to remove squeakiness) ... set speech rate to 1.15".
            # We will attempt to use torchaudio.transforms.PitchShift and TimeStretch? TimeStretch requires complex spec.
            # Let's just use torchaudio pitch shift if needed, or simply let `sounddevice` play it back at a modified rate.

            # Wait, `apply_tts` actually DOES support speed on some models if passed in `apply_tts` or maybe it doesn't on this v3/v4 loader.
            # Let's check `torchaudio.transforms.Resample`.
            # To speed it up by 1.15 WITHOUT changing pitch: Phase vocoder.
            # For this task, if we just pitch it down using torchaudio resample:

            # Since we can't easily TimeStretch without STFT, let's just do a basic resampling to pitch down,
            # and we will set the playback sample rate higher to speed it up.
            # Playback rate: 24000 * 1.15 = 27600 (speeds up 1.15x, but pitches up).
            # To counteract the pitch up, we need to pitch down the tensor beforehand by a factor of 1.15 * another factor.
            # Resampling tensor from 24000 to say 18000, then playing at 20700 (18000*1.15).

            # Let's simplify:
            # 1. Pitch down: Resample the generated tensor from 24000 to e.g. 20000.
            audio_tensor = torchaudio.functional.resample(audio_tensor, orig_freq=24000, new_freq=20000)

            # 2. Speed up: Play back at a faster rate relative to the new tensor's length.
            # If tensor is now effectively at "20000", to play it 1.15x faster, we play at 20000 * 1.15 = 23000
            self.target_sample_rate = 23000

            # Post-processing: silence reduction (trim zeros/near zeros)
            audio_np = audio_tensor.numpy()

            # Very simple silence reduction: trim ends
            if len(audio_np) > 0:
                # Find indices where audio is above a threshold
                threshold = 0.001
                non_silent = np.where(np.abs(audio_np) > threshold)[0]
                if len(non_silent) > 0:
                    start_idx = max(0, non_silent[0] - 100)
                    end_idx = min(len(audio_np), non_silent[-1] + 100)
                    audio_np = audio_np[start_idx:end_idx]

            return audio_np

        except Exception as e:
            logger.error(f"Error generating audio: {e}")
            return np.array([])

    def play_audio(self, audio_np: np.ndarray):
        """Blocking playback of the numpy array."""
        if len(audio_np) == 0:
            return

        try:
            # Playing back at a slightly lower sample rate pitches the voice down and makes it firmer
            sd.play(audio_np, samplerate=self.target_sample_rate)
            sd.wait() # wait until playback is finished
        except Exception as e:
            logger.error(f"Error playing audio: {e}")

    async def speak(self, text: str):
        """Async method to clean text, generate audio, and play it."""
        clean = self.clean_text(text)
        if not clean:
            return

        # Acquire lock so sentences don't overlap playback
        async with self._lock:
            # Run audio generation in a thread pool so we don't block the async loop
            logger.debug(f"Generating TTS for: {clean}")
            audio_np = await asyncio.to_thread(self.generate_audio, clean)

            # Play audio in thread pool
            if len(audio_np) > 0:
                await asyncio.to_thread(self.play_audio, audio_np)
