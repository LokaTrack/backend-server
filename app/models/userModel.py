from pydantic import BaseModel, EmailStr, Field #, validator
from typing import Optional
from datetime import datetime
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
    password_confirmation: str = Field(alias="password-confirmation")

    # @validator('password')
    # def password_min_length(cls, v):
    #     if len(v) < 8:
    #         raise ValueError('Password must be at least 8 characters')
    #     return v
    
    # @validator('password_confirmation')
    # def passwords_match(cls, v, values):
    #     if 'password' in values and v != values['password']:
    #         raise ValueError('Passwords do not match')
    #     return v
    
    class Config:
        # Allow population of fields using their original names (not aliases).
        populate_by_name = True

class UserLoginModel(BaseModel):
    email: EmailStr
    password: str

class UserModel(BaseModel):
    # generates a new UUID each time the User object is created.
    userId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    hashedPassword: str
    username: str
    role: UserRole = UserRole.DRIVER
    phoneNumber: Optional[str] = None
    # `default_factory` to generate the value dynamically
    registrationDate: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True

class UserResponseModel(BaseModel):
    email: str
    token: str