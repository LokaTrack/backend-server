from fastapi import HTTPException, status
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
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
        expire = datetime.utcnow() + expires_delta
    else:
        # data from .env always in string format
        expired_days = int(os.getenv("ACCESS_TOKEN_EXPIRED_DAYS", "30"))  # Default to 30 days if not set
        expire = datetime.utcnow() + timedelta(days=expired_days)
    
    issuer = os.getenv("APP_DOMAIN") or "lokatrack"
    dataToEncode = {
        "userId": data["userId"],
        "email": data["email"],
        "role": data["role"],
        "username": data["username"],
        "exp": expire,
        "iss": issuer
    }

    encoded_jwt = jwt.encode(dataToEncode, os.getenv("SECRET_KEY"), os.getenv("ALGORITHM"))
    return encoded_jwt

def verifyAccessToken(token: str):
    """Verify the JWT access token"""
    try:
        payload = jwt.decode(
            token,
            os.getenv("SECRET_KEY"),
            algorithms=[os.getenv("ALGORITHM")]
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
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
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
