import re
from typing import Tuple

def parse_llm_response(raw_text: str) -> Tuple[str, str]:
    """
    Separate the agent's hidden internal thoughts from external statements.
    Extracts text inside <thought>...</thought> as thought.
    Extracts text outside as visible output.
    Returns (thought, visible_output).
    """
    thought_pattern = re.compile(r'<thought>(.*?)</thought>', re.DOTALL)

    thoughts = thought_pattern.findall(raw_text)
    thought_text = "\n".join(t.strip() for t in thoughts)

    visible_text = thought_pattern.sub('', raw_text).strip()

    return thought_text, visible_text
