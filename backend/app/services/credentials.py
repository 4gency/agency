import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.core.security import decrypt_password, encrypt_password
from app.models.bot import Credentials, CredentialsInternal, CredentialsPublic

logger = logging.getLogger(__name__)


class CredentialsService:
    """Service for managing LinkedIn credentials."""

    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db

    def get_credentials_by_id(self, credentials_id: UUID) -> CredentialsInternal | None:
        """Get credentials by ID"""
        credentials = self.db.exec(
            select(Credentials).where(Credentials.id == credentials_id)
        ).first()

        if not credentials:
            return None

        credentials_internal = CredentialsInternal.model_validate(credentials)

        if credentials.password:
            credentials_internal.password = decrypt_password(credentials.password)

        return credentials_internal

    def get_user_credentials(self, user_id: UUID) -> list[CredentialsPublic]:
        """Get all credentials for a user"""
        credentials_list = self.db.exec(
            select(Credentials).where(Credentials.user_id == user_id)
        ).all()

        # Return list of CredentialsPublic with obfuscated information
        return [
            CredentialsPublic(
                id=cred.id,
                email=cred.obfuscated_email or cred.email,
                password=cred.obfuscated_password or "*******",
            )
            for cred in credentials_list
        ]

    def create_credentials(
        self, user_id: UUID, email: str, password: str
    ) -> CredentialsInternal:
        """Create new credentials"""
        # Check if credentials already exist for this user and email
        existing = self.db.exec(
            select(Credentials)
            .where(Credentials.user_id == user_id)
            .where(Credentials.email == email)
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credentials with this email already exist for this user",
            )

        # Create new credentials
        new_credentials = Credentials(
            user_id=user_id, email=email, password=encrypt_password(password)
        )

        # Generate obfuscated fields
        new_credentials.obfuscate_fields(password)

        # Save to database
        self.db.add(new_credentials)
        self.db.commit()
        self.db.refresh(new_credentials)

        # Return with decrypted password for immediate use
        internal = CredentialsInternal.model_validate(new_credentials)
        internal.password = password  # Plain password for immediate use
        return internal

    def update_credentials(
        self,
        credentials_id: UUID,
        user_id: UUID,
        email: str | None = None,
        password: str | None = None,
    ) -> CredentialsInternal:
        """Update existing credentials"""
        # Get existing credentials
        credentials = self.db.exec(
            select(Credentials)
            .where(Credentials.id == credentials_id)
            .where(Credentials.user_id == user_id)
        ).first()

        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credentials not found",
            )

        # Update fields if provided
        if email is not None:
            existing_email = self.db.exec(
                select(Credentials)
                .where(Credentials.email == email)
                .where(Credentials.user_id == user_id)
            ).first()
            if existing_email and email != credentials.email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="You already have another account registered with that email",
                )
            credentials.email = email
            credentials.obfuscate_email()

        if password is not None:
            credentials.password = encrypt_password(password)
            # Regenerate obfuscated fields
            credentials.obfuscate_password(password)

        # Save to database
        self.db.add(credentials)
        self.db.commit()
        self.db.refresh(credentials)

        # Return with decrypted password
        internal = CredentialsInternal.model_validate(credentials)
        internal.password = decrypt_password(credentials.password)

        return internal

    def delete_credentials(self, credentials_id: UUID, user_id: UUID) -> bool:
        """Delete credentials"""
        # Get existing credentials
        credentials = self.db.exec(
            select(Credentials)
            .where(Credentials.id == credentials_id)
            .where(Credentials.user_id == user_id)
        ).first()

        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credentials not found",
            )

        # Delete from database
        self.db.delete(credentials)
        self.db.commit()

        return True
