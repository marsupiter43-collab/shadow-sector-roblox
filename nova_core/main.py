import asyncio
import logging
import signal
import sys

from nova_core.engine.loop import AgentLoop

# Configure standard formatting for all logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("main")

async def cli_listener(agent: AgentLoop):
    """Listens for user input from the CLI without blocking."""
    loop = asyncio.get_event_loop()
    logger.info("CLI listener ready. Type your message and press Enter. Type 'quit' to exit.")

    while True:
        # Run standard input reading in a thread pool to avoid blocking the async event loop
        user_input = await loop.run_in_executor(None, sys.stdin.readline)
        text = user_input.strip()

        if text:
            if text.lower() in ('quit', 'exit'):
                logger.info("Exit command received.")
                # We can't cleanly break main loop here directly without passing a signal or flag
                # For this simple setup, we'll stop the agent loop.
                await agent.stop()
                break

            await agent.input_queue.put(text)

async def main():
    agent = AgentLoop()

    # Optional graceful shutdown handlers for SIGINT/SIGTERM (Unix-like)
    def shutdown_handler():
        logger.info("Shutdown signal received. Exiting...")
        asyncio.create_task(agent.stop())

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, shutdown_handler)
        except NotImplementedError:
            # Windows fallback
            pass

    # Start main agent loop (runs forever until stopped)
    agent_task = asyncio.create_task(agent.start())

    # Start the CLI listener
    cli_task = asyncio.create_task(cli_listener(agent))

    # Wait for both tasks to complete or get cancelled
    await asyncio.gather(agent_task, cli_task, return_exceptions=True)
    logger.info("Application shut down successfully.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
