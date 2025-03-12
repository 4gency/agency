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
from bot_session import BotSession

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
    status = "running"
    
    if bot_session:
        status = bot_session.status
    
    return {
        "status": "ok",
        "bot_status": status,
        "config_loaded": config is not None
    }


@app.post("/start")
async def start_bot(background_tasks: BackgroundTasks):
    """Start bot endpoint."""
    global bot_session
    
    if bot_session and bot_session.is_running():
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
        bot_session.stop()
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
        result = bot_session.process_user_action(action_id, action_data)
        return {"status": "success", "message": "Action processed", "result": result}
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
        bot_session.stop()
    
    sys.exit(0)


def run_bot():
    """Run the bot in a background task."""
    global bot_session, config
    
    if bot_session and bot_session.is_running():
        logger.warning("Bot is already running, ignoring start request")
        return
    
    try:
        logger.info("Starting bot session")
        bot_session = BotSession(
            api_key=config.backend_token,
            backend_url=config.backend_url,
            bot_id=config.bot_id,
            apply_limit=config.apply_limit
        )
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
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    
    # Start the API server
    logger.info(f"Starting Bot Mock API on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_config=log_config)


if __name__ == "__main__":
    main() 