"""Authentication controller with business logic."""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import User
from auth.repository import UserRepository
from auth.schemas import (
    PasswordChange,
    Token,
    UserCreate,
    UserLogin,
    UserUpdate,
    generate_user_id,
)
from auth.utils import (
    create_token_for_user,
    get_password_hash,
    verify_password,
)


class AuthController:
    """Controller for authentication operations."""

    def __init__(self):
        """Initialize the auth controller."""
        self.repository = UserRepository()

    async def register_user(
        self, session: AsyncSession, user_data: UserCreate
    ) -> User:
        """
        Register a new user.

        Args:
            session: Database session
            user_data: User registration data

        Returns:
            The created User object

        Raises:
            HTTPException: If email or username already exists
        """
        # Check if email already exists
        if await self.repository.email_exists(session, user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Check if username already exists
        if await self.repository.username_exists(session, user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )

        # Hash the password
        hashed_password = get_password_hash(user_data.password)

        # Create user object
        user_dict = {
            "id": generate_user_id(),
            "email": user_data.email,
            "username": user_data.username,
            "hashed_password": hashed_password,
            "is_active": True,
            "is_verified": False,
        }

        # Create user in database
        user = await self.repository.create(session, user_dict)
        return user

    async def authenticate_user(
        self, session: AsyncSession, login_data: UserLogin
    ) -> Token:
        """
        Authenticate a user and return a JWT token.

        Args:
            session: Database session
            login_data: User login credentials

        Returns:
            Token object with access token

        Raises:
            HTTPException: If credentials are invalid
        """
        # Find user by username or email
        user = await self.repository.get_by_username_or_email(
            session, login_data.username
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        # Create access token
        access_token, expires_in = create_token_for_user(user.id, user.username)

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
        )

    async def get_user_by_id(self, session: AsyncSession, user_id: str) -> User | None:
        """
        Get a user by ID.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            User object if found, None otherwise
        """
        return await self.repository.get(session, user_id)

    async def update_user_profile(
        self, session: AsyncSession, user_id: str, update_data: UserUpdate
    ) -> User:
        """
        Update user profile information.

        Args:
            session: Database session
            user_id: User ID
            update_data: User update data

        Returns:
            Updated User object

        Raises:
            HTTPException: If user not found or update conflicts with existing data
        """
        # Get existing user
        user = await self.repository.get(session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Check if new email already exists (if email is being updated)
        if update_data.email and update_data.email != user.email:
            if await self.repository.email_exists(session, update_data.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use",
                )

        # Check if new username already exists (if username is being updated)
        if update_data.username and update_data.username != user.username:
            if await self.repository.username_exists(session, update_data.username):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken",
                )

        # Update user
        update_dict = update_data.model_dump(exclude_unset=True)
        updated_user = await self.repository.update(session, user_id, update_dict)

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user",
            )

        return updated_user

    async def change_password(
        self, session: AsyncSession, user_id: str, password_data: PasswordChange
    ) -> bool:
        """
        Change user password.

        Args:
            session: Database session
            user_id: User ID
            password_data: Password change data

        Returns:
            True if password changed successfully

        Raises:
            HTTPException: If user not found or current password is incorrect
        """
        # Get user
        user = await self.repository.get(session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Verify current password
        if not verify_password(password_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        # Hash new password
        new_hashed_password = get_password_hash(password_data.new_password)

        # Update password
        await self.repository.update(
            session, user_id, {"hashed_password": new_hashed_password}
        )

        return True

    async def verify_user_email(self, session: AsyncSession, user_id: str) -> User:
        """
        Verify a user's email address.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            Updated User object

        Raises:
            HTTPException: If user not found
        """
        user = await self.repository.verify_user_email(session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user
