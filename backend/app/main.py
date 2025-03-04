import logging

import stripe
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings
from app.core.scheduled_tasks import start_scheduled_tasks, stop_scheduled_tasks

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def custom_generate_unique_id(route: APIRoute) -> str:
    """
    Generates a unique identifier for each route based on the first tag and the route's name.
    """
    tag = getattr(route, "tags", ["untagged"])[0]
    return f"{tag}-{route.name}"


def init_stripe() -> None:
    """
    Initializes Stripe if the secret key is set.
    Raises an error if running in a non-local environment and no key is provided.
    """
    if hasattr(settings, "STRIPE_SECRET_KEY") and settings.STRIPE_SECRET_KEY:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.api_version = "2022-11-15"
        logger.info("Stripe initialized")
    elif settings.ENVIRONMENT != "local":
        logger.warning("Stripe secret key is not set in a non-local environment")
    else:
        logger.info("Stripe not initialized (local environment)")


def create_application() -> FastAPI:
    """
    Creates and configures the FastAPI application.
    """
    # Initialize Stripe
    init_stripe()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        generate_unique_id_function=custom_generate_unique_id,
    )

    # Set all CORS enabled origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include the API router
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
