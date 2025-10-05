"""User model for authentication and authorization."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlmodel import Column, Field, SQLModel


class User(SQLModel, table=True, extend_existing=True):
    """User model for authentication."""

    __tablename__: str = "users"

    id: str = Field(primary_key=True, max_length=50, index=True)
    email: str = Field(
        ...,
        sa_column=Column(String, unique=True, index=True),
        description="User email address",
    )
    username: str = Field(
        ...,
        sa_column=Column(String(50), unique=True, index=True),
        description="Username for login",
    )
    hashed_password: str = Field(..., description="Bcrypt hashed password")
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, default=True),
        description="Whether the user account is active",
    )
    is_verified: bool = Field(
        default=False,
        sa_column=Column(Boolean, default=False),
        description="Whether the user email is verified",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
        ),
    )
