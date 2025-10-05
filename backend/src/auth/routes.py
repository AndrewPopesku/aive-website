"""Authentication routes for user management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.controller import AuthController
from auth.dependencies import get_current_active_user
from auth.models import User
from auth.schemas import (
    PasswordChange,
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)
from database.session import get_session

router = APIRouter()
auth_controller = AuthController()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Register a new user.

    - **email**: Valid email address
    - **username**: Unique username (3-50 characters)
    - **password**: Strong password (min 8 chars, must include uppercase, lowercase, and digit)
    """
    user = await auth_controller.register_user(session, user_data)
    return user


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    session: AsyncSession = Depends(get_session),
):
    """
    Login with username/email and password.

    Returns a JWT access token that should be included in the Authorization header
    for protected endpoints as: `Bearer <token>`

    - **username**: Username or email address
    - **password**: User password
    """
    token = await auth_controller.authenticate_user(session, login_data)
    return token


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get current authenticated user information.

    Requires valid JWT token in Authorization header.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Update current user profile.

    Requires valid JWT token in Authorization header.

    - **email**: New email address (optional)
    - **username**: New username (optional)
    """
    updated_user = await auth_controller.update_user_profile(
        session, current_user.id, update_data
    )
    return updated_user


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Change user password.

    Requires valid JWT token in Authorization header.

    - **current_password**: Current password
    - **new_password**: New password (min 8 chars, must include uppercase, lowercase, and digit)
    """
    success = await auth_controller.change_password(
        session, current_user.id, password_data
    )

    if success:
        return {"message": "Password changed successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password",
        )


@router.post("/verify-email/{user_id}", response_model=UserResponse)
async def verify_email(
    user_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Verify user email address.

    This is a simplified endpoint. In production, you would:
    1. Send a verification email with a unique token
    2. User clicks link with token
    3. Verify token and mark email as verified

    - **user_id**: User ID to verify
    """
    user = await auth_controller.verify_user_email(session, user_id)
    return user
