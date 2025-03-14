#!/usr/bin/env python3
import os
import signal
import sys
import threading
import logging
import uvicorn
from typing import Dict, Any
from fastapi import FastAPI
import time

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

# Initialize FastAPI app
app = FastAPI(title="LinkedIn Bot Mock API")

# Create a state dictionary for storing app-wide variables
app_state: Dict[str, Any] = {
    "bot_session": None,
    "pending_actions": {},  # Will store action_id -> processed_data for pending actions
    "current_action_id": None,  # Store the current action ID separately for easier access
}

# Initialize config as a module-level variable
config = None

# Initialize a threading lock for bot_session access
session_lock = threading.RLock()


# Create a safe way to access the bot session
def get_bot_session():
    """Get the bot session from app state, with proper locking"""
    with session_lock:
        return app_state.get("bot_session")


def set_bot_session(session):
    """Set the bot session in app state, with proper locking"""
    with session_lock:
        app_state["bot_session"] = session


# Functions for managing pending actions
def add_pending_action(action_id, data):
    """Add an action to the pending queue"""
    with session_lock:
        app_state["pending_actions"][action_id] = data
        logger.info(f"Added action {action_id} to pending queue")

        # If this action matches the current_action_id, process it immediately
        if action_id == app_state.get("current_action_id") and app_state.get(
            "bot_session"
        ):
            logger.info(f"Found matching action for current_action_id: {action_id}")
            try:
                bot_session = app_state["bot_session"]
                bot_session.resolve_user_action(action_id, data)
                # Remove from pending after processing
                if action_id in app_state["pending_actions"]:
                    del app_state["pending_actions"][action_id]
                    logger.info(
                        f"Processed and removed action {action_id} from pending queue"
                    )
            except Exception as e:
                logger.error(
                    f"Error immediately processing matching action {action_id}: {e}",
                    exc_info=True,
                )


def get_pending_action(action_id):
    """Get a pending action if it exists"""
    with session_lock:
        return app_state["pending_actions"].get(action_id)


def remove_pending_action(action_id):
    """Remove a pending action after it's processed"""
    with session_lock:
        if action_id in app_state["pending_actions"]:
            del app_state["pending_actions"][action_id]
            logger.info(f"Removed action {action_id} from pending queue")


# Functions to set and get current action ID - accessible from bot_session
def set_current_action_id(action_id):
    """Set the current action ID that the bot is waiting for"""
    with session_lock:
        logger.info(f"Setting current_action_id to: {action_id}")
        app_state["current_action_id"] = action_id

        # Check if the action is already in the pending queue
        if action_id in app_state["pending_actions"] and app_state.get("bot_session"):
            logger.info(
                f"Found pending action matching new current_action_id: {action_id}"
            )
            try:
                data = app_state["pending_actions"][action_id]
                bot_session = app_state["bot_session"]
                bot_session.resolve_user_action(action_id, data)
                # Remove from pending after processing
                del app_state["pending_actions"][action_id]
                logger.info(
                    f"Processed and removed action {action_id} from pending queue"
                )
            except Exception as e:
                logger.error(
                    f"Error processing pending action {action_id}: {e}", exc_info=True
                )


def get_current_action_id():
    """Get the current action ID that the bot is waiting for"""
    with session_lock:
        return app_state.get("current_action_id")


# Function to check for and process any pending actions
def process_pending_actions(provided_bot_session=None):
    """Process any actions that were received but couldn't be processed

    Args:
        provided_bot_session: Optional bot session object provided directly from the caller
                             (used when called from bot_session.py to avoid lookup issues)
    """
    # Use the provided bot_session if given, otherwise try to get it from app_state
    bot_session = (
        provided_bot_session if provided_bot_session is not None else get_bot_session()
    )
    current_id = get_current_action_id()

    if not bot_session or not current_id:
        logger.warning(
            "Can't process pending actions: bot_session or current_action_id is None"
        )
        return False

    with session_lock:
        # Only copy the keys to avoid modifying during iteration
        pending_action_ids = list(app_state["pending_actions"].keys())

    if pending_action_ids:
        logger.info(f"Found {len(pending_action_ids)} pending actions to process")

    # If current_action_id is in pending actions, process it
    if current_id in pending_action_ids:
        try:
            with session_lock:
                data = app_state["pending_actions"][current_id]

            logger.info(f"Processing matching pending action: {current_id}")
            bot_session.resolve_user_action(current_id, data)

            with session_lock:
                if current_id in app_state["pending_actions"]:
                    del app_state["pending_actions"][current_id]
                    logger.info(
                        f"Successfully processed and removed action {current_id}"
                    )

            return True
        except Exception as e:
            logger.error(
                f"Error processing pending action {current_id}: {e}", exc_info=True
            )

    return False


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    global config

    # Get the bot session using the helper function
    bot_session = get_bot_session()

    # More detailed status checking
    is_ready = bot_session is not None
    status = bot_session.status.value if bot_session else "not_started"
    config_loaded = config is not None

    # Log the health check in more detail
    logger.info(
        f"Health check: bot_initialized={is_ready}, status={status}, config_loaded={config_loaded}"
    )

    response = {
        "status": "ok" if is_ready else "initializing",
        "bot_status": status,
        "config_loaded": config_loaded,
        "ready": is_ready,
        "timestamp": time.time(),
    }

    return response


@app.post("/action/{action_id}")
async def user_action(action_id: str, action_data: Dict[str, Any]):
    """
    Endpoint for receiving user action responses.

    Params:
        action_id: Action identifier
        action_data: Action response data (full BotUserAction model from backend)
    """
    # Get the bot session using the helper function
    bot_session = get_bot_session()

    # Log to debug potential thread/scope issues
    logger.info(
        f"Action request received for ID {action_id}, bot_session exists: {bot_session is not None}"
    )

    # Extract user_input from action_data and transform to expected format
    # The bot_session code expects an 'input' field, but backend sends 'user_input'
    user_input = action_data.get("user_input")

    # Transform the data to match what bot_session is expecting
    processed_data = {"input": user_input}

    logger.info(f"Received action data: {action_data}")
    logger.info(f"Transformed to: {processed_data}")

    # Always add to pending queue first
    add_pending_action(action_id, processed_data)

    # Now try direct processing if bot session is available
    if not bot_session:
        logger.warning(
            f"Bot session appears to be None in the action endpoint for {action_id}"
        )
        logger.warning(
            "Added action to pending queue - bot thread will process it later"
        )
        return {"status": "success", "message": "Action queued for processing"}

    try:
        # Log the action receipt
        logger.info(f"Trying direct processing for action ID: {action_id}")
        logger.info(f"Bot status is: {bot_session.status.value}")

        # Check if this action matches the current_action_id
        current_id = get_current_action_id()
        if current_id == action_id:
            # Great! We can try to process directly
            logger.info(
                f"Direct processing: action ID {action_id} matches current_action_id"
            )
            try:
                bot_session.resolve_user_action(action_id, processed_data)
                # Remove from pending if processed directly
                remove_pending_action(action_id)
                return {"status": "success", "message": "Action processed directly"}
            except Exception as e:
                logger.error(f"Error in direct processing: {e}", exc_info=True)
                return {
                    "status": "success",
                    "message": "Action queued (processing error)",
                }
        else:
            logger.warning(
                f"Action ID mismatch: received {action_id} but current is {current_id}"
            )
            return {"status": "success", "message": "Action queued (ID mismatch)"}
    except Exception as e:
        logger.error(f"Error in action endpoint: {e}", exc_info=True)
        return {"status": "success", "message": f"Action queued due to error: {str(e)}"}


def signal_handler(sig, frame):
    """Handle termination signals."""
    logger.info("Received termination signal, shutting down...")

    # Get the bot session
    bot_session = get_bot_session()
    if bot_session:
        bot_session._change_status(BotStatus.STOPPING)

    sys.exit(0)


def start_bot_thread():
    """Run the bot in a background thread."""
    global config

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
        logger.info("Initializing bot session object...")
        bot_session = BotSession(config, api_client)

        # Store the bot session in the app state
        set_bot_session(bot_session)

        logger.info(f"Bot session initialized with status: {bot_session.status.value}")

        # Run the bot
        print("\n" + "=" * 50)
        print("BOT THREAD STARTING - LOGS SHOULD APPEAR BELOW")
        print("=" * 50 + "\n")
        bot_session.run()
    except Exception as e:
        logger.error(f"Error in bot execution: {e}", exc_info=True)
        # Make sure bot_session is None if there was an error
        set_bot_session(None)


def main():
    """Main entry point."""
    global config

    # Explicitly set bot_session to None
    set_bot_session(None)

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
    logger.info("Starting bot thread...")
    bot_thread = threading.Thread(target=start_bot_thread, daemon=True)
    bot_thread.start()
    logger.info("Bot thread started")

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
else:
    # This allows the bot_session module to access our functions
    # when it imports this module
    logger.info("Main module imported for pending actions access")
