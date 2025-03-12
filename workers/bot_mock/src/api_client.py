#!/usr/bin/env python3
from typing import Dict, Optional, Tuple
import os

import requests
import backoff
import yaml

from logger import setup_logger

logger = setup_logger("api_client")


class APIClient:
    """Client for communicating with the backend."""

    def __init__(self, base_url: str, api_key: str):
        """
        Initializes the API client.

        Args:
            base_url: Backend base URL
            api_key: Authentication token
        """
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"api-key": api_key}
        self.config_yaml = None
        self.resume_yaml = None

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.RequestException, ConnectionError),
        max_tries=5,
        jitter=backoff.full_jitter,
    )
    def _make_request(
        self, method: str, endpoint: str, data: Optional[Dict] = None
    ) -> Dict:
        """
        Makes an HTTP request with exponential retry.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: Relative endpoint
            data: Data to send (optional)

        Returns:
            Dict with API response or error
        """
        url = f"{self.base_url}/api/v1/bot-webhook{endpoint}"

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(
                    url, headers=self.headers, json=data, timeout=30
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error in request {method} {endpoint}: {e}")
            if hasattr(e, "response") and e.response and hasattr(e.response, "text"):
                logger.error(f"Error response: {e.response.text}")
            raise

    def get_config(self) -> Tuple[str, str]:
        """
        Gets the user's configurations and resume.

        Returns:
            Tuple with configurations and resume in YAML format
        """
        logger.info("Getting user configurations")
        try:
            response = self._make_request("GET", "/config")

            if "user_config" not in response or "user_resume" not in response:
                logger.error(f"Incomplete API response: {response}")
                raise ValueError("API response does not contain the expected fields")

            # Log the size of YAMLs for debug
            user_config = response["user_config"]
            user_resume = response["user_resume"]

            logger.info(f"Received user_config with {len(user_config)} characters")
            logger.info(f"Received user_resume with {len(user_resume)} characters")

            # Save configurations to file for debug
            configs_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "configs"
            )
            os.makedirs(configs_dir, exist_ok=True)

            config_path = os.path.join(configs_dir, "user_config.yaml")
            with open(config_path, "w") as f:
                f.write(user_config)
            logger.info(f"Configuration saved at {config_path}")

            resume_path = os.path.join(configs_dir, "user_resume.yaml")
            with open(resume_path, "w") as f:
                f.write(user_resume)
            logger.info(f"Resume saved at {resume_path}")

            # Check if YAMLs are valid without assigning the result
            try:
                # Just check if parsing works
                yaml.safe_load(user_config)
                yaml.safe_load(user_resume)
                logger.info("Configurations obtained and validated successfully")
            except yaml.YAMLError as e:
                logger.error(f"Invalid YAML received from API: {e}")
                # We don't raise exception here to allow the bot to continue
                # The actual YAML processing will happen in bot_session.py

            return user_config, user_resume

        except Exception as e:
            logger.error(f"Error getting configurations: {e}")
            # Return empty but valid YAMLs in case of error
            return "{}", "{}"

    def register_apply(self, apply_data: Dict) -> Dict:
        """
        Registers a job application.

        Args:
            apply_data: Application data

        Returns:
            Dict with API response
        """
        logger.info(f"Registering application: {apply_data}")
        return self._make_request("POST", "/apply", apply_data)

    def create_event(
        self,
        event_type: str,
        message: str,
        severity: str = "info",
        details: Optional[Dict] = None,
    ) -> Dict:
        """
        Creates an event in the backend.

        Args:
            event_type: Event type
            message: Event message
            severity: Event severity (info, warning, error)
            details: Additional details

        Returns:
            Dict with API response
        """
        event_data = {
            "type": event_type,
            "message": message,
            "severity": severity,
            "details": details or {},
        }
        logger.info(f"Creating event: {event_data}")
        return self._make_request("POST", "/events", event_data)

    def request_user_action(
        self, action_type: str, description: str, input_field: Optional[str] = None
    ) -> Dict:
        """
        Requests a user action.

        Args:
            action_type: Action type (PROVIDE_2FA, SOLVE_CAPTCHA, ANSWER_QUESTION)
            description: Description of the action for the user
            input_field: Field for user input (optional)

        Returns:
            Dict with API response containing the action ID
        """
        # Convert action_type to lowercase as expected by the API
        # (API expects 'provide_2fa' but our enum uses 'PROVIDE_2FA')
        lowercase_action_type = action_type.lower()

        action_data = {
            "action_type": lowercase_action_type,
            "description": description,
            "input_field": input_field,
        }
        logger.info(f"Requesting user action: {action_data}")
        return self._make_request("POST", "/user-actions", action_data)
