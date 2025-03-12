#!/usr/bin/env python3
import os
import signal
import sys
import threading
import logging
import uvicorn
from typing import Dict, Any
from fastapi import FastAPI, HTTPException

from config import load_config
from logger import setup_logger
from bot_session import BotSession, BotStatus
from api_client import APIClient

# Configure root logger to ensure all logs go to console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Set up our specific logger
logger = setup_logger("main", console_output=True, file_output=True)

# Make sure all important modules' loggers also show output
bot_logger = logging.getLogger("bot_session")
bot_logger.setLevel(logging.INFO)
bot_logger.propagate = True

api_logger = logging.getLogger("api_client")
api_logger.setLevel(logging.INFO)
api_logger.propagate = True

app = FastAPI(title="LinkedIn Bot Mock API")

# Global variables
bot_session = None
config = None


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    status = "not_started"

    if bot_session:
        status = bot_session.status.value

    return {"status": "ok", "bot_status": status, "config_loaded": config is not None}


@app.post("/action/{action_id}")
async def user_action(action_id: str, action_data: Dict[str, Any]):
    """
    Endpoint for receiving user action responses.

    Params:
        action_id: Action identifier
        action_data: Action response data (typically containing an input field)
    """
    global bot_session

    if not bot_session:
        raise HTTPException(status_code=404, detail="Bot not started")

    try:
        bot_session.resolve_user_action(action_id, action_data)
        return {"status": "success", "message": "Action processed"}
    except Exception as e:
        logger.error(f"Error processing user action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def signal_handler(sig, frame):
    """Handle termination signals."""
    logger.info("Received termination signal, shutting down...")

    global bot_session
    if bot_session:
        bot_session._change_status(BotStatus.STOPPING)

    sys.exit(0)


def start_bot_thread():
    """Run the bot in a background thread."""
    global bot_session, config

    try:
        logger.info("Starting bot session")

        # Make sure we have a valid config
        if not config:
            logger.error("No valid configuration found. Cannot start bot.")
            return

        # First create the API client
        api_client = APIClient(
            base_url=config.backend_url, api_key=config.backend_token
        )

        # Then create the bot session with config and api_client
        bot_session = BotSession(config, api_client)

        # Run the bot
        print("\n" + "=" * 50)
        print("BOT THREAD STARTING - LOGS SHOULD APPEAR BELOW")
        print("=" * 50 + "\n")
        bot_session.run()
    except Exception as e:
        logger.error(f"Error in bot execution: {e}")


def main():
    """Main entry point."""
    global config

    # Print a very visible message to confirm our logging is working
    print("\n" + "=" * 80)
    print("STARTING BOT MOCK - LOGS WILL APPEAR BELOW")
    print("=" * 80 + "\n")

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Load configuration
    try:
        config = load_config()
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)

    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=start_bot_thread, daemon=True)
    bot_thread.start()

    # Configure more explicit logging for uvicorn
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,  # Critical - don't disable existing loggers
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "access": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": True},
            "uvicorn.error": {"level": "INFO", "propagate": True},
            "uvicorn.access": {
                "handlers": ["access"],
                "level": "INFO",
                "propagate": False,
            },
            # Make sure our app loggers are also included
            "bot_session": {"level": "INFO", "propagate": True},
            "api_client": {"level": "INFO", "propagate": True},
            "main": {"level": "INFO", "propagate": True},
        },
        "root": {"level": "INFO", "handlers": ["default"], "propagate": True},
    }

    # Get port from config or environment
    port = config.api_port if config else int(os.environ.get("API_PORT", "8080"))

    # Start the API server
    logger.info(f"Starting Bot Mock API on port {port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_config=logging_config,
        log_level="info",
    )


if __name__ == "__main__":
    main()
