"""
AutoCodit Agent - Authentication System

JWT-based authentication with GitHub OAuth integration.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import User, APIKey

logger = structlog.get_logger()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthenticationError(HTTPException):
    """Authentication error"""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthService:
    """Authentication service"""
    
    def __init__(self):
        self.settings = get_settings()
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(hours=24)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.settings.JWT_SECRET,
            algorithm="HS256"
        )
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.settings.JWT_SECRET,
                algorithms=["HS256"]
            )
            return payload
        
        except JWTError as e:
            logger.warning("Invalid JWT token", error=str(e))
            return None
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def generate_api_key(self) -> tuple[str, str, str]:
        """Generate new API key"""
        # Generate random key
        key_bytes = secrets.token_urlsafe(32)
        prefix = "ac_" + secrets.token_urlsafe(8)[:8]
        full_key = f"{prefix}_{key_bytes}"
        
        # Hash for storage
        key_hash = self.hash_api_key(full_key)
        
        return full_key, key_hash, prefix
    
    async def authenticate_user(self, db: AsyncSession, token: str) -> Optional[User]:
        """Authenticate user by JWT token"""
        payload = self.verify_token(token)
        if not payload:
            return None
        
        github_id = payload.get("sub")
        if not github_id:
            return None
        
        # Get user from database
        query = select(User).where(User.github_id == github_id, User.is_active == True)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        return user
    
    async def authenticate_api_key(self, db: AsyncSession, api_key: str) -> Optional[tuple[User, APIKey]]:
        """Authenticate user by API key"""
        key_hash = self.hash_api_key(api_key)
        
        # Get API key from database
        query = select(APIKey).where(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        )
        result = await db.execute(query)
        api_key_obj = result.scalar_one_or_none()
        
        if not api_key_obj or api_key_obj.is_expired:
            return None
        
        # Get associated user
        user_query = select(User).where(
            User.id == api_key_obj.user_id,
            User.is_active == True
        )
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Update usage statistics
        api_key_obj.last_used_at = datetime.now(timezone.utc)
        api_key_obj.usage_count += 1
        await db.commit()
        
        return user, api_key_obj


# Global auth service instance
auth_service = AuthService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    
    token = credentials.credentials
    
    # Try JWT authentication first
    user = await auth_service.authenticate_user(db, token)
    if user:
        return user
    
    # Try API key authentication
    auth_result = await auth_service.authenticate_api_key(db, token)
    if auth_result:
        user, api_key = auth_result
        return user
    
    raise AuthenticationError("Invalid authentication credentials")


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user (optional, returns None if not authenticated)"""
    
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    # TODO: Implement role checking
    # For now, all authenticated users are considered admins in their scope
    return current_user


def require_organization_access(
    organization_id: str,
    required_role: str = "member"
):
    """Require access to specific organization"""
    def _check_access(current_user: User = Depends(get_current_user)) -> User:
        # TODO: Check organization membership and role
        return current_user
    
    return _check_access