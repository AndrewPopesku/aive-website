"""Authentication utilities for password hashing and JWT token management."""

from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from base.config import get_settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Get settings
settings = get_settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to check against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: The plain text password to hash

    Returns:
        The hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary containing the payload data
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )

    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    """
    Decode and verify a JWT access token.

    Args:
        token: The JWT token string to decode

    Returns:
        Dictionary containing the decoded payload, or None if invalid
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


def create_token_for_user(user_id: str, username: str) -> tuple[str, int]:
    """
    Create an access token for a user.

    Args:
        user_id: The user's ID
        username: The user's username

    Returns:
        Tuple of (token_string, expires_in_seconds)
    """
    access_token_expires = timedelta(minutes=settings.jwt_expire_minutes)

    token_data = {"sub": user_id, "username": username}

    access_token = create_access_token(
        data=token_data, expires_delta=access_token_expires
    )

    return access_token, settings.jwt_expire_minutes * 60
