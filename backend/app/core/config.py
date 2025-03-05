import secrets
import warnings
from typing import Annotated, Any, Literal

from pydantic import (
    AnyUrl,
    BeforeValidator,
    HttpUrl,
    computed_field,
    model_validator,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    FRONTEND_HOST: str = "http://localhost:5173"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    STRIPE_SECRET_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    PROJECT_NAME: str
    SENTRY_DSN: HttpUrl | None = None
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> MultiHostUrl:
        return MultiHostUrl.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    MONGODB_SERVER: str
    MONGODB_PORT: int = 27017
    MONGODB_DB: str
    MONGODB_USER: str
    MONGODB_PASSWORD: str

    S3_ENDPOINT_URL: str
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    S3_CONFIGS_BUCKET: str = "configs"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def MONGODB_URI(self) -> MultiHostUrl:
        scheme = "mongodb"
        if "." in self.MONGODB_SERVER:
            scheme = "mongodb+srv"  # DNS (supports SRV)
        return MultiHostUrl.build(
            scheme=scheme,
            username=self.MONGODB_USER,
            password=self.MONGODB_PASSWORD,
            host=self.MONGODB_SERVER,
            port=self.MONGODB_PORT,
        )

    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: str | None = None
    EMAILS_FROM_NAME: str | None = None

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48

    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    EMAIL_TEST_USER: str = "test@example.com"
    EMAIL_TEST_USER_SUBSCRIBER: str = "test_subscriber@example.com"
    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: str

    # Kubernetes Configuration
    KUBERNETES_IN_CLUSTER: bool = False
    KUBERNETES_NAMESPACE: str = "bot-jobs"
    KUBERNETES_SERVICE_ACCOUNT: str = "bot-service-account"
    KUBERNETES_RESOURCE_PREFIX: str = "job-apply-bot"
    CLOUD_STORAGE_SECRET_NAME: str = "cloud-storage-credentials"

    # Bot Configuration
    BOT_IMAGE: str = "lambdagency/job-apply-bot:latest"
    BOT_API_KEY: str = "changethis"
    API_BASE_URL: str = "http://localhost:8000/api/v1"
    BOT_LOG_LEVEL: str = "INFO"

    # Kubernetes Resources
    BOT_DEFAULT_CPU_REQUEST: str = "500m"
    BOT_DEFAULT_MEMORY_REQUEST: str = "1Gi"
    BOT_DEFAULT_CPU_LIMIT: str = "1000m"
    BOT_DEFAULT_MEMORY_LIMIT: str = "2Gi"

    @model_validator(mode="after")
    def _validate_kubernetes_config(self) -> Self:
        if self.ENVIRONMENT == "production" and not self.KUBERNETES_IN_CLUSTER:
            warnings.warn(
                "Running in production mode but KUBERNETES_IN_CLUSTER is set to False",
                stacklevel=1,
            )

        self._check_default_secret("BOT_API_KEY", self.BOT_API_KEY)
        return self

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "production":
                raise ValueError(message)
            else:
                warnings.warn(message, stacklevel=1)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )

        return self


settings = Settings()  # type: ignore
