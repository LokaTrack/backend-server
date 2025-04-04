from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid
from enum import Enum

class UserRole(str, Enum):
    DRIVER = "driver"
    ADMIN = "admin"
    PENDING = "pending"
    INACTIVE = "inactive"

class UserCreateModel(BaseModel):
    email: EmailStr
    username: str
    password: str
    passwordConfirmation: str
    
    class Config:
        # Allow population of fields using their original names (not aliases).
        populate_by_name = True

class UserLoginModel(BaseModel):
    email: EmailStr
    password: str

class UpdateUsernameModel(BaseModel):
    username: str
    lastUpdate: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class updatePhoneNumberModel(BaseModel):
    phoneNumber: str
    lastUpdate: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UpdatePasswordModel(BaseModel):
    currentPassword: str
    newPassword: str
    newPasswordConfirmation: str
    lastUpdate: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserModel(BaseModel):
    # generates a new UUID each time the User object is created.
    userId: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    hashedPassword: str
    username: str
    role: UserRole = UserRole.DRIVER
    phoneNumber: Optional[str] = None
    profilePictureUrl: Optional[str] = None
    isEmailVerified: bool = False

    # `default_factory` to generate the value dynamically
    registrationDate: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    lastUpdate: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
     
    class Config:
        from_attributes = True
