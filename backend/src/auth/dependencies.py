"""FastAPI dependencies for authentication and authorization."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import User
from auth.schemas import TokenData
from auth.utils import decode_access_token
from database.session import get_session

# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Get the current authenticated user from the JWT token.

    Args:
        credentials: HTTP Authorization credentials containing the JWT token
        session: Database session

    Returns:
        The authenticated User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Extract token from credentials
    token = credentials.credentials

    # Decode and verify token
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    # Extract user ID from token
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Create token data
    token_data = TokenData(user_id=user_id, username=payload.get("username"))

    # Fetch user from database
    from sqlmodel import select

    statement = select(User).where(User.id == token_data.user_id)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current authenticated and active user.

    Args:
        current_user: The current user from get_current_user dependency

    Returns:
        The authenticated and active User object

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get the current authenticated, active, and verified user.

    Args:
        current_user: The current active user

    Returns:
        The authenticated, active, and verified User object

    Raises:
        HTTPException: If user email is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email to continue.",
        )
    return current_user


def verify_project_access(project_id_param: str = "project_id"):
    """
    Dependency factory to verify user has access to a project.
    
    This creates a dependency that can be used in routes to automatically
    check if the current user owns the specified project.
    
    Args:
        project_id_param: Name of the path parameter containing the project ID
    
    Returns:
        A FastAPI dependency function
    
    Usage:
        @router.get("/{project_id}")
        async def get_project(
            project_id: str,
            verified_project: dict = Depends(verify_project_access()),
            session: AsyncSession = Depends(get_session),
        ):
            # verified_project contains the project details
            return verified_project
    """
    async def _verify_access(
        project_id: str,
        current_user: User = Depends(get_current_active_user),
        session: AsyncSession = Depends(get_session),
    ) -> dict:
        """
        Verify that the current user has access to the project.
        
        Returns:
            The project details if access is granted
        
        Raises:
            HTTPException: If project not found or user doesn't have access
        """
        # Import here to avoid circular dependency
        from projects.controller import ProjectController
        
        controller = ProjectController()
        
        try:
            project_details = await controller.get_project_with_details(
                session, project_id
            )
        except HTTPException as e:
            # Re-raise if project not found
            raise e
        
        # Check ownership
        if project_details.get("user_id") != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this project",
            )
        
        return project_details
    
    return _verify_access
