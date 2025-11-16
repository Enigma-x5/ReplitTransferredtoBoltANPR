from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import authenticate_user, create_access_token
from src.config import settings
from src.database import get_db
from src.schemas.auth import LoginRequest, AuthToken
from src.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=AuthToken)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, request.email, request.password)

    if not user:
        logger.warning("Failed login attempt", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value}, expires_delta=access_token_expires
    )

    logger.info("User logged in", user_id=str(user.id), email=user.email)

    return AuthToken(
        access_token=access_token,
        token_type="Bearer",
        expires_in=settings.JWT_EXPIRATION_MINUTES * 60,
    )
