from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timedelta, timezone
import random
import string

class ResetPasswordRequestModel(BaseModel):
    email: EmailStr

class ResetPasswordModel(BaseModel):
    email: EmailStr
    otp: str
    newPassword: str
    newPasswordConfirmation: str

class OtpVerificationModel(BaseModel):
    otp: str
    expiresAt: datetime
    
    @staticmethod
    def generate(expiry_minutes: int = 10):
        """Generate a new OTP for password reset"""
        otp = ''.join(random.choices(string.digits, k=6))  # 6-digit OTP
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)
        
        return OtpVerificationModel(
            otp=otp,
            expiresAt=expires_at
        )