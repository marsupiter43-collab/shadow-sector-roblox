from pydantic import BaseModel, Field

class StateManager(BaseModel):
    mood: str = Field(default="calm", description="Current mood of the agent: calm, curious, analytical, bored")
    energy_level: int = Field(default=100, ge=0, le=100, description="Energy level from 0 to 100")
    idle_seconds: int = Field(default=0, description="Seconds since last external input")

    def reset_idle(self) -> None:
        """Reset idle timer on external interaction."""
        self.idle_seconds = 0

    def tick_idle(self, seconds: int) -> None:
        """Increase idle timer."""
        self.idle_seconds += seconds

    def update_energy(self, delta: int) -> None:
        """Update energy level and constrain to 0-100."""
        self.energy_level = max(0, min(100, self.energy_level + delta))

    def change_mood(self, new_mood: str) -> None:
        """Update the agent's mood."""
        allowed_moods = ["calm", "curious", "analytical", "bored"]
        if new_mood in allowed_moods:
            self.mood = new_mood
