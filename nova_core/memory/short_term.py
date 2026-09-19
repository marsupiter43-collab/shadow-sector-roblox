from typing import List, Tuple

class ShortTermMemory:
    def __init__(self, max_size: int = 50):
        self.max_size = max_size
        self.history: List[Tuple[str, str]] = []

    def add_interaction(self, role: str, text: str) -> None:
        self.history.append((role, text))
        if len(self.history) > self.max_size:
            self.history.pop(0)

    def get_context_window(self, limit: int = 5) -> List[Tuple[str, str]]:
        return self.history[-limit:]
