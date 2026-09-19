# Nova Core

Nova is an autonomous cognitive AI agent with proactive behavior, internal monologue (chain-of-thought), internal emotional/state management, and asynchronous event handling. The core runs fully locally without cloud dependencies.

## Setup

1. Install dependencies:
   ```bash
   pip install -r nova_core/requirements.txt
   ```

2. Make sure Ollama is running locally (e.g. `http://localhost:11434`) with the chosen model (default is `llama3`).

## Usage

Start the agent:

```bash
PYTHONPATH=. python nova_core/main.py
```

Type into the console to interact with the agent. Type `quit` or `exit` to shut down the application.
