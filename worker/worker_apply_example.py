from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import wraps
from typing import Literal
import os

import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
BACKEND_API_KEY = os.getenv("BACKEND_API_KEY", "my_secret_api_key")
SESSION_ID = os.getenv("SESSION_ID", "uuid4-session-id")
USER_ID = os.getenv("USER_ID", "uuid4-user-id")

class optional_instance:
    """
    A descriptor that automatically injects the singleton instance into
    the method when it's called on the class.
    """
    def __init__(self, func):
        self.func = func
        wraps(func)(self)

    def __get__(self, instance, owner):
        if instance is None:
            instance = owner()
        return lambda *args, **kwargs: self.func(instance, *args, **kwargs)

class Singleton(type):
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

@dataclass
class Apply(metaclass=Singleton):
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_time: int = 0  # in seconds
    status: Literal["awaiting", "started", "success", "failed"] = "awaiting"
    pdf_text: str | None = None
    failed: bool = False
    failed_reason: str | None = None
    company_name: str | None = None
    linkedin_url: str | None = None

    @optional_instance
    def __reset(self):
        """Resets the instance to its default state."""
        self.started_at = datetime.now(timezone.utc)
        self.total_time = 0
        self.status = "awaiting"
        self.pdf_text = None
        self.failed = False
        self.failed_reason = None
        self.company_name = None
        self.linkedin_url = None
    
    def __send_to_backend(self, data):
        """Sends the current state to the backend."""
        response = requests.post(
            f"{BACKEND_URL}/api/v1/users/{USER_ID}/bots/{SESSION_ID}/apply", 
            headers={"Authorization": f"Bearer {BACKEND_API_KEY}"},
            json=data, 
        )
        response.raise_for_status()

    @optional_instance
    def __save(self):
        """Saves the current state"""
        retries = 5
        data = self.__dict__
        data["started_at"] = data["started_at"].isoformat()
        while retries > 0:
            try:
                self.__send_to_backend(data)
                break
            except Exception as e:
                retries -= 1
                if retries == 0:
                    print(f"Failed to save state: {e}")
                else:
                    print(f"Retrying to save state: {e}")

    @optional_instance
    def __handle_not_finished(self):
        """
        Handles the case where a new apply is started without finishing the current one.
        Marks the instance as failed and then finishes it.
        """
        msg = "A new apply was instantiated without finishing the existing one."
        self.failed = True
        if self.failed_reason:
            self.failed_reason += "\n" + msg
        else:
            self.failed_reason = msg
        self.finish()

    @optional_instance
    def finish(self):
        """
        Finishes the apply process by calculating total time,
        saving the state, and then resetting the instance.
        """
        end_time = datetime.now(timezone.utc)
        self.total_time = int((end_time - self.started_at).total_seconds())
        self.__save()
        self.__reset()

    @optional_instance
    def start(self):
        """
        Starts the apply process. If the current process isn't awaiting,
        it flags the previous one as not finished.
        """
        if self.status != "awaiting":
            self.__handle_not_finished()
        self.status = "started"
