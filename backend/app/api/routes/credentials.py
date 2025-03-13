import functools
from collections.abc import Callable
from typing import Any, TypeVar
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import EmailStr
from sqlmodel import SQLModel

from app.api.deps import CurrentUser, SessionDep
from app.models.core import ErrorMessage, Message
from app.services.credentials import CredentialsService

# Tipo genérico para a função decorada
T = TypeVar("T")


# Decorador para tratamento padronizado de exceções
def handle_service_exceptions(func: Callable[..., T]) -> Callable[..., T]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return func(*args, **kwargs)
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e

    return wrapper


# Modelos para as rotas
class CredentialsCreate(SQLModel):
    """Modelo para criação de credenciais"""

    email: EmailStr
    password: str


class CredentialsUpdate(SQLModel):
    """Modelo para atualização de credenciais"""

    email: EmailStr | None = None
    password: str | None = None


class CredentialsPublic(SQLModel):
    """Modelo para exibição pública de credenciais"""

    id: UUID
    email: str  # Email ofuscado exibido ao usuário
    password: str  # Senha ofuscada exibida ao usuário (geralmente asteriscos)


# Definição do modelo de resposta para a listagem de credenciais
class CredentialsResponse(SQLModel):
    total: int
    items: list[CredentialsPublic]


router = APIRouter()


@router.get(
    "/",
    response_model=CredentialsResponse,
    responses={401: {"model": ErrorMessage, "description": "Authentication error"}},
)
def get_user_credentials(*, session: SessionDep, user: CurrentUser) -> Any:
    """
    Get all credentials for the current user.
    """
    credentials_service = CredentialsService(session)
    credentials_list = credentials_service.get_user_credentials(user_id=user.id)

    return {"total": len(credentials_list), "items": credentials_list}


@router.post(
    "/",
    response_model=CredentialsPublic,
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        400: {"model": ErrorMessage, "description": "Validation error"},
    },
)
@handle_service_exceptions
def create_credentials(
    *, session: SessionDep, user: CurrentUser, credentials_in: CredentialsCreate
) -> Any:
    """
    Create new LinkedIn credentials.
    """
    credentials_service = CredentialsService(session)
    credentials = credentials_service.create_credentials(
        user_id=user.id,
        email=credentials_in.email,
        password=credentials_in.password,
    )

    return CredentialsPublic(
        id=credentials.id,
        email=credentials.obfuscated_email,
        password=credentials.obfuscated_password,
    )


@router.put(
    "/{credentials_id}",
    response_model=CredentialsPublic,
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        404: {"model": ErrorMessage, "description": "Credentials not found"},
    },
)
@handle_service_exceptions
def update_credentials(
    *,
    session: SessionDep,
    user: CurrentUser,
    credentials_id: UUID,
    credentials_in: CredentialsUpdate,
) -> Any:
    """
    Update LinkedIn credentials.
    """
    credentials_service = CredentialsService(session)
    credentials = credentials_service.update_credentials(
        credentials_id=credentials_id,
        user_id=user.id,
        email=credentials_in.email,
        password=credentials_in.password,
    )

    return CredentialsPublic(
        id=credentials.id,
        email=credentials.obfuscated_email,
        password=credentials.obfuscated_password,
    )


@router.delete(
    "/{credentials_id}",
    response_model=Message,
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        404: {"model": ErrorMessage, "description": "Credentials not found"},
    },
)
@handle_service_exceptions
def delete_credentials(
    *, session: SessionDep, user: CurrentUser, credentials_id: UUID
) -> Any:
    """
    Delete LinkedIn credentials.
    """
    credentials_service = CredentialsService(session)

    result = credentials_service.delete_credentials(
        credentials_id=credentials_id, user_id=user.id
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Credentials not found"
        )

    return {"message": "Credentials deleted successfully"}
