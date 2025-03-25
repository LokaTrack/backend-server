from passlib.context import CryptContext
from datetime import datetime, timedelta
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

    dataToEncode = {
        "email": data["email"],
        "role": data["role"],
        "username": data["username"]
    }

    # if expires_delta is provided, use it
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # data from .env always in string format
        expired_days = int(os.getenv("ACCESS_TOKEN_EXPIRED_DAYS"), 30)  # Default to 30 days if not set
        expire = datetime.utcnow() + timedelta(days=expired_days)
        
    dataToEncode.update({"exp": expire})
    encoded_jwt = jwt.encode(dataToEncode, os.getenv("SECRET_KEY"), os.getenv("ALGORITHM"))
    return encoded_jwt