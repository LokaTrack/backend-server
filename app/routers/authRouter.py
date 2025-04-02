from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.models.userModel import UserCreateModel, UserLoginModel
from app.models.authModel import ResetPasswordRequestModel, ResetPasswordModel
from app.services.authService import registerUser, loginUser, requestResetPassword, resetPassword

router = APIRouter(prefix="/api/v1", tags=["Authentication"])

@router.post("/register", status_code=201)
async def register(userDataInput: UserCreateModel):
    """Register a new user"""
    try:
        result = await registerUser(userDataInput)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )
    
@router.post("/login")
async def login(userDataLogin: UserLoginModel):
    """Login an existing user and return a token"""
    try:
        result = await loginUser(userDataLogin)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )
    
@router.post("/request-reset-password")
async def request_reset_password(resetRequest: ResetPasswordRequestModel):
    """Request password reset and send OTP via email"""
    try:
        result = await requestResetPassword(resetRequest.email)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )
    
@router.post("/reset-password")
async def reset_password(resetPasswordData: ResetPasswordModel):
    """Request password reset and send OTP via email"""
    try:
        result = await resetPassword(resetPasswordData)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )
