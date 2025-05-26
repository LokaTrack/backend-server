from fastapi import HTTPException, status
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
from typing import Optional
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# JWT settings
ACCESS_TOKEN_EXPIRED_DAYS = os.getenv("ACCESS_TOKEN_EXPIRED_DAYS", "30")  # Default to 30 days if not set
ALGORITHM = os.getenv("ALGORITHM", "HS256")  # Default to HS256 if not set
SECRET_KEY = os.getenv("SECRET_KEY")
APP_DOMAIN = os.getenv("APP_DOMAIN",  "lokatrack")

# Password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    default="bcrypt",
    deprecated="auto"
)

def verifyPassword(plainPassword, hashedPassword):
    """Verify a password against a hash"""
    return pwd_context.verify(plainPassword, hashedPassword)

def getPasswordHash(password):
    """Generate a password hash"""
    return pwd_context.hash(password)

def createAccessToken(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    # dataToEncode = data.copy()

    # if expires_delta is provided, use it
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # data from .env always in string format
        expired_days = int(ACCESS_TOKEN_EXPIRED_DAYS) 
        expire = datetime.now(timezone.utc) + timedelta(days=expired_days)

    dataToEncode = {
        "userId": data.get("userId"),
        "email": data.get("email"),
        "role": data.get("role"),
        "username": data.get("username"),
        "exp": expire,
        "iss": APP_DOMAIN,
        "lokataniSession": data.get("lokataniSession", None)  # Optional field
    }

    encoded_jwt = jwt.encode(
        dataToEncode, 
        SECRET_KEY,
        ALGORITHM)
    return encoded_jwt

def verifyAccessToken(token: str):
    """Verify the JWT access token"""
    try:
        payload = jwt.decode(
            token, SECRET_KEY, ALGORITHM
        )
        return payload  # Return the decoded payload if valid

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "fail",
                "message": "Token kedaluwarsa, silakan login kembali.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "fail",
                "message": "Token tidak valid",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "fail",
                "message": f"Error verifikasi token: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    # except JWTError:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Token tidak valid atau telah kedaluwarsa",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )


async def get_ws_user(token: str):
    """Authenticate WebSocket connections using JWT token"""
    try:
        # Decode token
        payload = jwt.decode(
            token, SECRET_KEY, ALGORITHM
        )

        return payload

    except Exception as e:
        logger.error(f"Error authenticating WebSocket user: {str(e)}")
        return f"Error authenticating user"
