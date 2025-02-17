import sentry_sdk
import stripe
from fastapi import FastAPI
from fastapi.routing import APIRoute
from sentry_sdk.types import Event, Hint
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


def filter_transactions(event: Event, _: Hint) -> Event | None:
    url_string: str = event.get("request", {}).get("url", "")  # type: ignore

    if "health-check" in url_string:
        return None

    return event


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(
        dsn=str(settings.SENTRY_DSN),
        enable_tracing=True,
        environment=settings.ENVIRONMENT,
        before_send_transaction=filter_transactions,
    )

if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY
elif settings.ENVIRONMENT != "local":
    raise ValueError("Stripe secret key is not set")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
