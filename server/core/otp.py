"""
OTP generation and verification logic.
"""
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.config import get_settings
from server.models.otp import OTP

_otp_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_otp_code() -> str:
    """Generate a 6-digit numeric OTP."""
    return f"{secrets.randbelow(1000000):06d}"


async def create_and_store_otp(session: AsyncSession, email: str, purpose: str) -> str:
    """Generate a new OTP, store it in the database, and return the plain OTP code."""
    plain_otp = generate_otp_code()
    otp_hash = _otp_pwd_ctx.hash(plain_otp)
    
    # 10 minutes expiration
    expires_at = datetime.now(UTC) + timedelta(minutes=10)
    
    otp_record = OTP(
        email=email,
        otp_hash=otp_hash,
        purpose=purpose,
        expires_at=expires_at,
        verified=False
    )
    session.add(otp_record)
    await session.commit()
    return plain_otp


async def verify_otp_code(session: AsyncSession, email: str, otp_code: str, purpose: str) -> bool:
    """Verify an OTP code against the database. Marks it as verified if successful."""
    # Find the latest unverified, unexpired OTP for this email and purpose
    now = datetime.now(UTC)
    result = await session.execute(
        select(OTP)
        .where(
            OTP.email == email,
            OTP.purpose == purpose,
            OTP.verified == False,
            OTP.expires_at > now
        )
        .order_by(OTP.created_at.desc())
        .limit(1)
    )
    otp_record = result.scalar_one_or_none()
    
    if not otp_record:
        return False
        
    if _otp_pwd_ctx.verify(otp_code, otp_record.otp_hash):
        otp_record.verified = True
        await session.commit()
        return True
        
    return False


def generate_verification_token(email: str, purpose: str) -> str:
    """Generate a short-lived JWT token that proves the email was verified via OTP."""
    settings = get_settings()
    # 15 minutes to complete the registration/reset after verifying OTP
    expire = datetime.now(UTC) + timedelta(minutes=15)
    payload = {
        "email": email,
        "purpose": purpose,
        "exp": expire,
        "type": "otp_verification"
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_verification_token(token: str, expected_purpose: str) -> str | None:
    """Decode a verification token and return the email if valid and matches purpose."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "otp_verification":
            return None
        if payload.get("purpose") != expected_purpose:
            return None
        return payload.get("email")
    except jwt.InvalidTokenError:
        return None
