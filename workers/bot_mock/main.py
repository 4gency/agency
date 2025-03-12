#!/usr/bin/env python3
import asyncio
import os
import signal
import sys
import time
import threading
import logging
import uvicorn
import yaml
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from config import load_config
from logger import setup_logger
from bot_session import BotSession, BotStatus
from api_client import APIClient
from models import BotSessionStatus

logger = setup_logger("main")
app = FastAPI(title="LinkedIn Bot Mock API")

# Global variables
bot_session = None
config = None


@app.on_event("startup")
async def startup_event():
    """FastAPI startup event handler."""
    global config
    try:
        config = load_config()
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    status = "not_started"
    
    if bot_session:
        status = bot_session.status.value
    
    return {
        "status": "ok",
        "bot_status": status,
        "config_loaded": config is not None
    }


@app.post("/start")
async def start_bot(background_tasks: BackgroundTasks):
    """Start bot endpoint."""
    global bot_session
    
    if bot_session and bot_session.status == BotStatus.RUNNING:
        return {"status": "error", "message": "Bot is already running"}
    
    try:
        background_tasks.add_task(run_bot)
        return {"status": "success", "message": "Bot starting in the background"}
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/stop")
async def stop_bot():
    """Stop bot endpoint."""
    global bot_session
    
    if not bot_session:
        return {"status": "error", "message": "Bot not started"}
    
    try:
        # Change the bot status to stopping
        bot_session._change_status(BotStatus.STOPPING)
        return {"status": "success", "message": "Bot stopping"}
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        return {"status": "error", "message": str(e)}


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


@app.post("/fake-configs")
async def set_fake_configs(config_data: Dict[str, Any]):
    """
    Endpoint for setting fake configurations for testing.
    Used only for debugging.
    """
    try:
        # Create configs directory if it doesn't exist
        configs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs")
        os.makedirs(configs_dir, exist_ok=True)
        
        # Save configs to file
        if "user_config" in config_data:
            with open(os.path.join(configs_dir, "user_config.yaml"), "w") as f:
                f.write(config_data["user_config"])
        
        if "user_resume" in config_data:
            with open(os.path.join(configs_dir, "user_resume.yaml"), "w") as f:
                f.write(config_data["user_resume"])
        
        return {"status": "success", "message": "Fake configurations set"}
    except Exception as e:
        logger.error(f"Error setting fake configurations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def signal_handler(sig, frame):
    """Handle termination signals."""
    logger.info("Received termination signal, shutting down...")
    
    global bot_session
    if bot_session:
        bot_session._change_status(BotStatus.STOPPING)
    
    sys.exit(0)


def run_bot():
    """Run the bot in a background task."""
    global bot_session, config
    
    if bot_session and bot_session.status == BotStatus.RUNNING:
        logger.warning("Bot is already running, ignoring start request")
        return
    
    try:
        logger.info("Starting bot session")
        
        # Make sure we have a valid config
        if not config:
            logger.error("No valid configuration found. Cannot start bot.")
            return
        
        # First create the API client
        api_client = APIClient(
            base_url=config.backend_url,
            api_key=config.backend_token
        )
        
        # Then create the bot session with config and api_client
        bot_session = BotSession(config, api_client)
        bot_session.run()
    except Exception as e:
        logger.error(f"Error in bot execution: {e}")


def main():
    """Main entry point."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Get port from config or environment
    try:
        config = load_config()
        port = config.api_port
    except Exception:
        port = int(os.environ.get("API_PORT", "8080"))
    
    # Configure logging for uvicorn
    logging_config = {
        "version": 1,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(levelname)s - %(message)s"
            },
            "access": {
                "format": "%(asctime)s - %(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.error": {"level": "INFO"},
            "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
        }
    }
    
    # Start the API server
    logger.info(f"Starting Bot Mock API on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_config=logging_config)


if __name__ == "__main__":
    main() 