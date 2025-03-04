from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

import base64
import hashlib
from cryptography.fernet import Fernet

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)



def _get_fernet():
    """
    Gera uma instância de Fernet baseada na SECRET_KEY.
    Utiliza SHA256 para assegurar que sempre teremos 32 bytes
    ao codificar base64.
    """
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    key = base64.urlsafe_b64encode(key)
    return Fernet(key)

def encrypt_password(password: str) -> str:
    """
    Criptografa a senha em texto plano.
    Retorna a senha criptografada (string base64).
    """
    f = _get_fernet()
    token = f.encrypt(password.encode("utf-8"))
    return token.decode("utf-8")

def decrypt_password(encrypted_password: str) -> str:
    """
    Descriptografa a senha que foi criptografada anteriormente.
    Retorna a senha em texto plano.
    """
    f = _get_fernet()
    plaintext = f.decrypt(encrypted_password.encode("utf-8"))
    return plaintext.decode("utf-8")