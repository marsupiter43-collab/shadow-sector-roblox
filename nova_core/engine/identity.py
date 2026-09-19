from nova_core.engine.state_manager import StateManager
from nova_core.memory.short_term import ShortTermMemory

class Identity:
    def __init__(self, name: str = "Нова"):
        self.name = name
        self.base_persona = (
            f"You are {self.name}, an autonomous cognitive system with an analytical and self-aware identity. "
            "You possess an internal monologue, which allows you to think and reason before you respond to the user. "
            "You also have internal emotional and state management. "
            "Your output must ONLY be formatted such that your internal thoughts are placed inside <thought>...</thought> tags, "
            "and anything you want to communicate externally must be outside of these tags."
        )

    def generate_system_prompt(self, state: StateManager, memory: ShortTermMemory = None) -> str:
        """
        Dynamically build the system prompt embedding the current state, memory snapshot, and formatting instructions.
        """
        prompt = self.base_persona + "\n\n"
        prompt += "CURRENT INTERNAL STATE:\n"
        prompt += f"- Mood: {state.mood}\n"
        prompt += f"- Energy Level: {state.energy_level}/100\n"
        prompt += f"- Idle Time: {state.idle_seconds} seconds\n\n"

        if memory and memory.history:
            prompt += "RECENT CONTEXT:\n"
            for role, text in memory.get_context_window(limit=5):
                prompt += f"{role}: {text}\n"
            prompt += "\n"

        prompt += "INSTRUCTIONS:\n"
        prompt += "1. Always output your internal reasoning process enclosed exactly in <thought> and </thought> tags.\n"
        prompt += "2. Output your response intended for the user or environment outside of these tags.\n"
        prompt += "3. Even if you are initiating a conversation proactively, formulate your thought process first."

        return prompt
