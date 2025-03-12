#!/usr/bin/env python3
import time
import random
import threading
import uuid
from enum import Enum
from typing import Dict, Any

from faker import Faker
import yaml

from logger import setup_logger
from models import BotApplyStatus, UserActionType  # Import both from models

logger = setup_logger("bot_session")
faker = Faker()


class BotStatus(Enum):
    """Possible bot states."""

    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPING = "stopping"


class ApplyStatus(Enum):
    """Possible application states."""

    SUCCESS = "success"
    FAILED = "failed"


class JobInfo:
    """Simulated job information."""

    def __init__(self):
        """Generates a simulated job with random data."""
        self.id = str(uuid.uuid4())
        self.title = faker.job()
        self.company = faker.company()
        self.url = f"https://linkedin.com/jobs/view/{faker.numerify('########')}"
        self.location = faker.city()
        self.description = faker.paragraph(nb_sentences=5)
        self.posted_at = faker.date_time_between(start_date="-30d", end_date="now")

    def to_dict(self) -> Dict[str, Any]:
        """Converts the job to a dictionary."""
        return {
            "job_id": self.id,
            "job_title": self.title,
            "job_url": self.url,
            "company_name": self.company,
            "location": self.location,
            "description": self.description,
            "posted_at": self.posted_at.strftime("%Y-%m-%d %H:%M:%S"),
        }


class BotSession:
    """Bot session that simulates the behavior of the real bot."""

    def __init__(self, config, api_client):
        """
        Initializes the bot session.

        Args:
            config: Bot configuration
            api_client: Client for API communication
        """
        self.config = config
        self.api_client = api_client
        self.status = BotStatus.STARTING

        # Application counter
        self.total_applied = 0
        self.total_success = 0
        self.total_failed = 0

        # Flags for pause control
        self.paused = threading.Event()
        self.should_stop = threading.Event()

        # Flag to wait for user action
        self.waiting_for_action = threading.Event()
        self.current_action_id = None
        self.action_response = None

        # YAML configurations
        self.user_config = None
        self.user_resume = None

    def run(self) -> None:
        """Runs the simulated bot."""
        try:
            # Print startup banner
            print("\n" + "#" * 80)
            print(" " * 30 + "BOT SESSION STARTING")
            print("#" * 80 + "\n")

            # Send start event
            self._change_status(BotStatus.STARTING)
            self.api_client.create_event(
                "starting",
                "Starting application bot",
                "info",
                {"bot_id": self.config.bot_id},
            )

            # Get user configurations
            logger.info("-" * 60)
            logger.info("STEP 1: LOADING USER CONFIGURATIONS AND RESUME")
            logger.info("-" * 60)
            try:
                config_yaml, resume_yaml = self.api_client.get_config()

                # Load configurations
                try:
                    self.user_config = yaml.safe_load(config_yaml)
                    logger.info("User configuration loaded successfully")
                except yaml.YAMLError as e:
                    logger.error(f"Error loading YAML configuration: {e}")
                    self.user_config = {}

                try:
                    self.user_resume = yaml.safe_load(resume_yaml)
                    logger.info("User resume loaded successfully")
                except yaml.YAMLError as e:
                    logger.error(f"Error loading YAML resume: {e}")
                    self.user_resume = {}

                # Check if we have the minimum necessary configurations
                if not self.user_config:
                    logger.warning("User configuration is empty or invalid")

            except Exception as e:
                logger.error(f"Failed to get user configurations: {e}")
                self.user_config = {}
                self.user_resume = {}

            # Simulate LinkedIn login
            logger.info("-" * 60)
            logger.info("STEP 2: LOGGING INTO LINKEDIN")
            logger.info("-" * 60)
            self._simulate_login()

            # Change to running status
            self._change_status(BotStatus.RUNNING)
            self.api_client.create_event(
                "running",
                "Bot started successfully and running",
                "info",
                {"status": "running", "bot_version": "1.0.0"},
            )

            # Simulate navigation and applications
            logger.info("-" * 60)
            logger.info("STEP 3: STARTING JOB SEARCH AND APPLICATIONS")
            logger.info("-" * 60)
            self._simulate_job_search_and_apply()

            # Finalize the bot
            logger.info("-" * 60)
            logger.info("STEP 4: FINALIZING BOT EXECUTION")
            logger.info("-" * 60)
            self._finalize_bot()

        except Exception as e:
            logger.error(f"Error during bot execution: {e}", exc_info=True)
            self._handle_failure(str(e))

    def _change_status(self, new_status: BotStatus) -> None:
        """
        Changes the bot status.

        Args:
            new_status: New bot status
        """
        logger.info(f"Changing status from {self.status.value} to {new_status.value}")
        self.status = new_status

        # Configure events related to status
        if new_status == BotStatus.PAUSED:
            self.paused.set()
        elif new_status == BotStatus.RUNNING:
            self.paused.clear()
        elif new_status == BotStatus.WAITING:
            self.waiting_for_action.set()
        elif (
            new_status == BotStatus.STOPPING
            or new_status == BotStatus.COMPLETED
            or new_status == BotStatus.FAILED
        ):
            self.should_stop.set()
            self.paused.clear()  # Unblock paused threads so they can finish
            self.waiting_for_action.set()  # Unblock threads waiting for action

    def _simulate_login(self) -> None:
        """Simulates the LinkedIn login process."""
        # Event for navigating to login page
        self.api_client.create_event(
            "navigating",
            "Navigating to LinkedIn login page",
            "info",
            {"url": "https://www.linkedin.com/login"},
        )

        # Delay to simulate page loading
        time.sleep(2)

        # Randomly decide if 2FA is needed (increased from 30% to 70% chance)
        needs_2fa = random.random() < 0.7

        if needs_2fa:
            # Request 2FA code
            logger.info("=" * 60)
            logger.info("2FA VERIFICATION REQUIRED FOR LOGIN")
            logger.info("=" * 60)
            self._change_status(BotStatus.WAITING)

            # Send waiting event
            self.api_client.create_event(
                "waiting",
                "Waiting for 2FA verification code",
                "info",
                {"reason": "2FA required"},
            )

            # Request user action
            response = self.api_client.request_user_action(
                UserActionType.PROVIDE_2FA.value,
                "Please provide the LinkedIn two-factor authentication code",
                "2fa_code",
            )

            # Store the current action ID
            self.current_action_id = response["id"]

            # Wait for user response
            logger.info(
                f"Waiting for user response for action {self.current_action_id}"
            )
            self.waiting_for_action.wait(timeout=300)  # 5 minute timeout

            if not self.action_response:
                logger.warning("Time limit exceeded for user action")
                # Registrar erro de 2FA, mas continuar a execução
                self.api_client.create_event(
                    "verification_timeout",
                    "2FA verification code not provided in time",
                    "warning",
                    {"verification_type": "login_2fa"},
                )
                # Limpar flags para continuar
                self.waiting_for_action.clear()
                self.current_action_id = None

                # Simular login mesmo assim (é apenas um mock)
                logger.info("Continuing without 2FA (mock simulation)")
            else:
                # Reset flags
                self.waiting_for_action.clear()
                code = self.action_response.get("input", "")
                logger.info(f"2FA code received: {code}")
                self.action_response = None
                self.current_action_id = None

                # Simulating code validation
                time.sleep(2)

            # Successful login event with 2FA
            self.api_client.create_event(
                "logged_in", "Successfully logged into LinkedIn using 2FA", "info"
            )
        else:
            # Event for filling credentials
            self.api_client.create_event("login", "Filling login credentials", "info")

            # Delay to simulate filling
            time.sleep(1)

            # Form submission event
            self.api_client.create_event("form_submit", "Submitting login form", "info")

            # Delay to simulate login processing
            time.sleep(2)

            # Successful login event
            self.api_client.create_event(
                "logged_in", "Successfully logged into LinkedIn", "info"
            )

    def _simulate_job_search_and_apply(self) -> None:
        """Simulates the job search and application process."""
        # Simulate navigation to search page
        self.api_client.create_event(
            "navigating",
            "Navigating to job search page",
            "info",
            {"url": "https://www.linkedin.com/jobs/"},
        )

        # Delay to simulate page loading
        time.sleep(2)

        # Simulate search with user terms
        # Check if user_config exists and provide defaults if necessary
        if self.user_config is None:
            logger.warning("User configuration is not available, using default values")
            positions = ["Software Developer"]
            locations = ["Remote"]
            company_blacklist = []
            title_blacklist = []
        else:
            logger.info(f"Using user configuration: {type(self.user_config)}")
            try:
                positions = self.user_config.get("positions", ["Software Developer"])
                # Validate positions
                if not positions or not isinstance(positions, list):
                    logger.warning(
                        f"Invalid position configuration: {positions}, using default"
                    )
                    positions = ["Software Developer"]
                logger.info(f"Configured positions: {positions}")

                locations = self.user_config.get("locations", ["Remote"])
                # Validate locations
                if not locations or not isinstance(locations, list):
                    logger.warning(
                        f"Invalid location configuration: {locations}, using default"
                    )
                    locations = ["Remote"]
                logger.info(f"Configured locations: {locations}")

                company_blacklist = self.user_config.get("company_blacklist", [])
                # Validate company_blacklist
                if company_blacklist is None or not isinstance(company_blacklist, list):
                    logger.warning(
                        f"Invalid company blacklist: {company_blacklist}, using empty list"
                    )
                    company_blacklist = []
                logger.info(f"Company blacklist: {company_blacklist}")

                title_blacklist = self.user_config.get("title_blacklist", [])
                # Validate title_blacklist
                if title_blacklist is None or not isinstance(title_blacklist, list):
                    logger.warning(
                        f"Invalid title blacklist: {title_blacklist}, using empty list"
                    )
                    title_blacklist = []
                logger.info(f"Title blacklist: {title_blacklist}")
            except Exception as e:
                logger.error(f"Error processing user configuration: {e}")
                positions = ["Software Developer"]
                locations = ["Remote"]
                company_blacklist = []
                title_blacklist = []

        # Ensure we have at least one value in each list for random.choice
        if not positions:
            positions = ["Software Developer"]
        if not locations:
            locations = ["Remote"]

        search_query = f"{random.choice(positions)} in {random.choice(locations)}"

        self.api_client.create_event(
            "search_started",
            f"Starting search for: {search_query}",
            "info",
            {"query": search_query},
        )

        # Delay to simulate search
        time.sleep(3)

        # Enter application loop until reaching limit or receiving command to stop
        while (
            self.total_applied < self.config.apply_limit
            and not self.should_stop.is_set()
        ):
            # Check if the bot is paused
            if self.paused.is_set():
                logger.info("Bot is paused, waiting for command to continue")
                self.paused.wait()  # Wait until bot is unpaused
                if self.should_stop.is_set():
                    break

            try:
                # Generate wait time between 10 and 60 seconds
                wait_time = random.randint(10, 60)
                logger.info(f"Waiting {wait_time} seconds before next application")

                # Wait, checking each second if the bot should stop
                for _ in range(wait_time):
                    if self.should_stop.is_set() or self.paused.is_set():
                        break
                    time.sleep(1)

                if self.should_stop.is_set():
                    break

                if self.paused.is_set():
                    continue

                # Simulate finding a job
                job = JobInfo()

                self.api_client.create_event(
                    "job_found",
                    f"Job found: {job.title} at {job.company}",
                    "info",
                    job.to_dict(),
                )

                # Delay to simulate opening the job
                time.sleep(2)

                # Check if company is blacklisted
                try:
                    if company_blacklist is None:
                        company_blacklist = []
                        logger.warning("company_blacklist is None, using empty list")

                    if any(
                        blacklisted.lower() in job.company.lower()
                        for blacklisted in company_blacklist
                    ):
                        logger.info(f"Company {job.company} is blacklisted, skipping")
                        self.api_client.create_event(
                            "job_skipped",
                            f"Job skipped: company {job.company} is blacklisted",
                            "info",
                            {"reason": "blacklisted_company"},
                        )
                        continue
                except Exception as e:
                    logger.error(f"Error checking company blacklist: {e}")

                # Check if title is blacklisted
                try:
                    if title_blacklist is None:
                        title_blacklist = []
                        logger.warning("title_blacklist is None, using empty list")

                    if any(
                        blacklisted.lower() in job.title.lower()
                        for blacklisted in title_blacklist
                    ):
                        logger.info(f"Title {job.title} is blacklisted, skipping")
                        self.api_client.create_event(
                            "job_skipped",
                            f"Job skipped: title {job.title} is blacklisted",
                            "info",
                            {"reason": "blacklisted_title"},
                        )
                        continue
                except Exception as e:
                    logger.error(f"Error checking title blacklist: {e}")

                # Simulate clicking the apply button
                self.api_client.create_event(
                    "apply_started",
                    f"Starting application for: {job.title} at {job.company}",
                    "info",
                    job.to_dict(),
                )

                # Apenas chance para CAPTCHA durante aplicação (5% chance)
                needs_captcha = random.random() < 0.05

                if needs_captcha:
                    # Request CAPTCHA solution
                    logger.info("CAPTCHA detected in application process")
                    self._change_status(BotStatus.WAITING)

                    # Send waiting event
                    self.api_client.create_event(
                        "waiting",
                        "CAPTCHA detected in application process",
                        "info",
                        {"reason": "captcha_detected"},
                    )

                    # Request user action
                    response = self.api_client.request_user_action(
                        UserActionType.SOLVE_CAPTCHA.value,
                        "Please solve the CAPTCHA to continue with the application",
                        "captcha_solution",
                    )

                    # Store the current action ID
                    self.current_action_id = response["id"]

                    # Wait for user response
                    logger.info(
                        f"Waiting for CAPTCHA solution from user for action {self.current_action_id}"
                    )
                    self.waiting_for_action.wait(timeout=300)  # 5 minute timeout

                    if not self.action_response:
                        logger.warning("Time limit exceeded for CAPTCHA solution")
                        # Registrar erro de CAPTCHA, mas continuar a execução
                        self.api_client.create_event(
                            "verification_timeout",
                            "CAPTCHA solution not provided in time",
                            "warning",
                            {"verification_type": "captcha"},
                        )
                        # Limpar flags para continuar
                        self.waiting_for_action.clear()
                        self.current_action_id = None

                        logger.info(
                            "Continuing application without CAPTCHA solution (mock simulation)"
                        )
                    else:
                        # Reset flags
                        self.waiting_for_action.clear()
                        captcha_solution = self.action_response.get("input", "")
                        logger.info(f"CAPTCHA solved: {captcha_solution}")
                        self.action_response = None
                        self.current_action_id = None

                    # Return to RUNNING status
                    self._change_status(BotStatus.RUNNING)
                    self.api_client.create_event(
                        "running",
                        "Continuing application after CAPTCHA resolution",
                        "info",
                    )

                # Simulate form filling
                self.api_client.create_event(
                    "form_filling", "Filling application form", "info"
                )

                # Delay to simulate filling
                time.sleep(random.uniform(3, 8))

                # 10% chance of application failure
                will_fail = random.random() < 0.1
                logger.info("=" * 80)
                logger.info(
                    f"APPLICATION RESULT: {'FAILURE (10% chance)' if will_fail else 'SUCCESS (90% chance)'}"
                )
                logger.info("=" * 80)

                apply_duration = random.randint(15, 120)  # Duration in seconds

                try:
                    if will_fail:
                        # Random application failure
                        failure_reasons = [
                            "Error in application form",
                            "Connection problems",
                            "Application already submitted previously",
                            "Job is no longer available",
                            "Profile incompatible with requirements",
                        ]
                        failed_reason = random.choice(failure_reasons)
                        logger.warning(f"SIMULATION FAILURE: {failed_reason}")

                        # Register the failure
                        apply_data = {
                            "status": BotApplyStatus.FAILED.value,
                            "total_time": apply_duration,
                            "job_title": job.title,
                            "job_url": job.url,
                            "company_name": job.company,
                            "failed_reason": failed_reason,
                        }

                        logger.info(
                            f"Registering failed application: {job.title} at {job.company}"
                        )
                        response = self.api_client.register_apply(apply_data)
                        logger.info(
                            f"Failed application recorded with ID: {response.get('id', 'unknown')}"
                        )

                        # Increment counters
                        self.total_applied += 1
                        self.total_failed += 1

                        # Send failure event
                        self.api_client.create_event(
                            "apply_failed",
                            f"Application failure: {failed_reason}",
                            "warning",
                            {
                                "job_title": job.title,
                                "company": job.company,
                                "reason": failed_reason,
                            },
                        )
                    else:
                        # Successful application
                        apply_data = {
                            "status": BotApplyStatus.SUCCESS.value,
                            "total_time": apply_duration,
                            "job_title": job.title,
                            "job_url": job.url,
                            "company_name": job.company,
                        }

                        logger.info(
                            f"Registering successful application: {job.title} at {job.company}"
                        )
                        response = self.api_client.register_apply(apply_data)
                        logger.info(
                            f"Successful application recorded with ID: {response.get('id', 'unknown')}"
                        )

                        # Increment counters
                        self.total_applied += 1
                        self.total_success += 1

                        # Send success event
                        self.api_client.create_event(
                            "apply_success",
                            f"Application successfully submitted for: {job.title} at {job.company}",
                            "info",
                            {"job_title": job.title, "company": job.company},
                        )

                    # Update progress with prominent logging
                    logger.info("\n" + "*" * 80)
                    logger.info("PROGRESS UPDATE:")
                    logger.info(
                        f"COMPLETED: {self.total_applied}/{self.config.apply_limit} APPLICATIONS"
                    )
                    logger.info(
                        f"SUCCESS RATE: {self.total_success}/{self.total_applied} ({round(self.total_success/max(1, self.total_applied)*100, 1)}%)"
                    )
                    logger.info(
                        f"PROGRESS: {round(self.total_applied / self.config.apply_limit * 100, 1)}% COMPLETE"
                    )
                    logger.info("*" * 80)

                    # Send progress update event to backend
                    self.api_client.create_event(
                        "progress_update",
                        f"Progress: {self.total_applied}/{self.config.apply_limit} applications completed",
                        "info",
                        {
                            "total_applied": self.total_applied,
                            "total_success": self.total_success,
                            "total_failed": self.total_failed,
                            "apply_limit": self.config.apply_limit,
                            "progress_percentage": round(
                                self.total_applied / self.config.apply_limit * 100, 1
                            ),
                        },
                    )
                except Exception as e:
                    logger.error(f"Error registering application: {e}", exc_info=True)
                    self.api_client.create_event(
                        "error",
                        f"Error registering application: {e}",
                        "error",
                        {"error_details": str(e)},
                    )

                # Check if we reached the limit
                if self.total_applied >= self.config.apply_limit:
                    logger.info(
                        f"Application limit reached ({self.config.apply_limit})"
                    )
                    self._change_status(BotStatus.STOPPING)
                    self.api_client.create_event(
                        "stopping",
                        f"Application limit reached: {self.config.apply_limit}",
                        "info",
                        {"apply_limit": self.config.apply_limit},
                    )
            except Exception as e:
                logger.error(f"Error during application: {e}", exc_info=True)

                # Report error as event
                self.api_client.create_event(
                    "error",
                    f"Error during application: {str(e)}",
                    "error",
                    {"error_details": str(e)},
                )

                # Continue trying
                continue

    def _finalize_bot(self) -> None:
        """Finalizes the bot and sends completion events."""
        # Check status to decide how to finalize
        if self.status == BotStatus.STOPPING:
            # Finalize as complete
            self._change_status(BotStatus.COMPLETED)

            success_rate = (
                0
                if self.total_applied == 0
                else round(self.total_success / self.total_applied * 100, 1)
            )

            # Completion event
            self.api_client.create_event(
                "completed",
                f"Bot completed successfully. Applications: {self.total_applied}, Success rate: {success_rate}%",
                "info",
                {
                    "total_applies": self.total_applied,
                    "successful_applies": self.total_success,
                    "failed_applies": self.total_failed,
                    "success_rate": f"{success_rate}%",
                },
            )

            logger.info(
                f"Bot completed successfully. Applications: {self.total_applied}, Success rate: {success_rate}%"
            )
        elif self.status == BotStatus.FAILED:
            # We already sent the failure event in _handle_failure
            logger.info("Bot finalized with failure status.")

    def _handle_failure(self, reason: str) -> None:
        """
        Handles a fatal bot failure.

        Args:
            reason: Failure reason
        """
        logger.error(f"Fatal bot failure: {reason}")

        # Change status to failure
        self._change_status(BotStatus.FAILED)

        # Send failure event
        self.api_client.create_event(
            "failed", f"Bot failure: {reason}", "error", {"reason": reason}
        )

    def resolve_user_action(self, action_id: str, data: Dict[str, Any]) -> None:
        """
        Resolves a user action.

        Args:
            action_id: Action ID
            data: User response data
        """
        if self.current_action_id == action_id:
            logger.info(f"User action resolved: {action_id}")
            self.action_response = data

            # Unblock the waiting thread
            self.waiting_for_action.set()

            # Send continuation event
            self.api_client.create_event(
                "user_action_completed",
                f"User action #{action_id} has been completed",
                "info",
                {"action_id": action_id},
            )

            # Return to running status
            self._change_status(BotStatus.RUNNING)
        else:
            logger.warning(
                f"Received response for action {action_id}, but current action is {self.current_action_id}"
            )
