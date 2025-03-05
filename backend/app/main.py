import logging

import sentry_sdk
import stripe
from fastapi import FastAPI
from fastapi.routing import APIRoute
from sentry_sdk.types import Event, Hint
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings
from app.core.scheduled_tasks import start_scheduled_tasks, stop_scheduled_tasks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def custom_generate_unique_id(route: APIRoute) -> str:
    """
    Generates a unique identifier for each route based on the first tag and the route's name.
    """
    return f"{route.tags[0]}-{route.name}"


def filter_transactions(event: Event, _: Hint) -> Event | None:
    """
    Filters out transactions based on the URL. For example, health-check transactions can be ignored.
    """
    url_string: str = event.get("request", {}).get("url", "")  # type: ignore

    if "health-check" in url_string:
        return None

    return event


def init_sentry() -> None:
    """
    Initializes Sentry if DSN is set and environment is not local.
    """
    if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
        sentry_sdk.init(
            dsn=str(settings.SENTRY_DSN),
            enable_tracing=True,
            environment=settings.ENVIRONMENT,
            before_send_transaction=filter_transactions,
        )


def init_stripe() -> None:
    """
    Initializes Stripe if the secret key is set.
    Raises an error if running in a non-local environment and no key is provided.
    """
    if settings.STRIPE_SECRET_KEY:
        stripe.api_key = settings.STRIPE_SECRET_KEY
    elif settings.ENVIRONMENT != "local":
        raise ValueError("Stripe secret key is not set")


def create_application() -> FastAPI:
    """
    Creates and configures the FastAPI application.
    """
    init_stripe()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        generate_unique_id_function=custom_generate_unique_id,
    )

    if settings.all_cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.all_cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Add event handlers for scheduled tasks
    @app.on_event("startup")
    def start_scheduler():
        logger.info("Starting scheduled tasks")
        start_scheduled_tasks()

    @app.on_event("shutdown")
    def stop_scheduler():
        logger.info("Stopping scheduled tasks")
        stop_scheduled_tasks()

    return app


app = create_application()
