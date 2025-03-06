from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import CurrentUser, SessionDep
from app.models.bot import CredentialsCreate, CredentialsPublic, CredentialsUpdate
from app.models.core import ErrorMessage, Message
from app.services.credentials import CredentialsService


# Definição do modelo de resposta que faltava
class CredentialsResponse(BaseModel):
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
def create_credentials(
    *, session: SessionDep, user: CurrentUser, credentials_in: CredentialsCreate
) -> Any:
    """
    Create new LinkedIn credentials.
    """
    credentials_service = CredentialsService(session)

    try:
        credentials = credentials_service.create_credentials(
            user_id=user.id,
            email=credentials_in.email,
            password=credentials_in.password,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return CredentialsPublic.model_validate(credentials)


@router.put(
    "/{credentials_id}",
    response_model=CredentialsPublic,
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        404: {"model": ErrorMessage, "description": "Credentials not found"},
    },
)
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

    try:
        credentials = credentials_service.update_credentials(
            credentials_id=credentials_id,
            user_id=user.id,
            email=credentials_in.email,
            password=credentials_in.password,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return CredentialsPublic.model_validate(credentials)


@router.delete(
    "/{credentials_id}",
    response_model=Message,
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        404: {"model": ErrorMessage, "description": "Credentials not found"},
    },
)
def delete_credentials(
    *, session: SessionDep, user: CurrentUser, credentials_id: UUID
) -> Any:
    """
    Delete LinkedIn credentials.
    """
    credentials_service = CredentialsService(session)

    try:
        result = credentials_service.delete_credentials(
            credentials_id=credentials_id, user_id=user.id
        )
    except HTTPException as e:
        raise e

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Credentials not found"
        )

    return {"message": "Credentials deleted successfully"}
