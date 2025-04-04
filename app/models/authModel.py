from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timedelta, timezone
import random
import string
import uuid

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
    
class EmailVerificationModel(BaseModel):
    lastUpdate: datetime
    emailVerificationToken: str
    emailVerificationTokenExpiry: datetime
    
    @staticmethod
    def generate(expiry_hours: int = 24):
        """Generate a new email verification token"""
        lastUpdate = datetime.now(timezone.utc)
        emailVerificationToken = ''.join(random.choices(string.ascii_letters + string.digits, k=64))
        emailVerificationTokenExpiry = datetime.now() + timedelta(hours=expiry_hours)
        
        return EmailVerificationModel(
            lastUpdate=lastUpdate,
            emailVerificationToken=emailVerificationToken,  
            emailVerificationTokenExpiry=emailVerificationTokenExpiry 
        )