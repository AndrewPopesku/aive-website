"""Authentication repository for user database operations."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from auth.models import User
from base.repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model database operations."""

    def __init__(self):
        """Initialize the User repository."""
        super().__init__(User)

    async def get_by_email(self, session: AsyncSession, email: str) -> User | None:
        """
        Get a user by email address.

        Args:
            session: Database session
            email: User email address

        Returns:
            User object if found, None otherwise
        """
        statement = select(User).where(User.email == email)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_username(self, session: AsyncSession, username: str) -> User | None:
        """
        Get a user by username.

        Args:
            session: Database session
            username: Username

        Returns:
            User object if found, None otherwise
        """
        statement = select(User).where(User.username == username)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def email_exists(self, session: AsyncSession, email: str) -> bool:
        """
        Check if an email already exists in the database.

        Args:
            session: Database session
            email: Email address to check

        Returns:
            True if email exists, False otherwise
        """
        user = await self.get_by_email(session, email)
        return user is not None

    async def username_exists(self, session: AsyncSession, username: str) -> bool:
        """
        Check if a username already exists in the database.

        Args:
            session: Database session
            username: Username to check

        Returns:
            True if username exists, False otherwise
        """
        user = await self.get_by_username(session, username)
        return user is not None

    async def get_by_username_or_email(
        self, session: AsyncSession, identifier: str
    ) -> User | None:
        """
        Get a user by username or email.

        Args:
            session: Database session
            identifier: Username or email address

        Returns:
            User object if found, None otherwise
        """
        statement = select(User).where(
            (User.username == identifier) | (User.email == identifier)
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def verify_user_email(
        self, session: AsyncSession, user_id: str
    ) -> User | None:
        """
        Mark a user's email as verified.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            Updated User object if found, None otherwise
        """
        user = await self.get(session, user_id)
        if user:
            user.is_verified = True
            await session.commit()
            await session.refresh(user)
        return user

    async def deactivate_user(
        self, session: AsyncSession, user_id: str
    ) -> User | None:
        """
        Deactivate a user account.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            Updated User object if found, None otherwise
        """
        user = await self.get(session, user_id)
        if user:
            user.is_active = False
            await session.commit()
            await session.refresh(user)
        return user
