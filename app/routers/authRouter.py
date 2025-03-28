from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from app.models.userModel import UserCreateModel, UserLoginModel
from app.services.authService import registerUser, loginUser, getUserProfile
from app.utils.auth import get_current_user

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

@router.get("/user")
async def getUser(currentUser: dict = Depends(get_current_user)):
    """Get user data"""
    try:    
        result = await getUserProfile(currentUser)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )
    