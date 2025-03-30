from fastapi import APIRouter, File, HTTPException, Depends, UploadFile, status, Form
from fastapi.responses import JSONResponse
from app.models.userModel import UpdatePasswordModel, updatePhoneNumberModel, UpdateUsernameModel
from app.utils.auth import get_current_user
from app.services.profileService import updatePasswordService, updatePhoneNumberService, updateUsernameService, getUserProfile, updateProfilePictureService

router = APIRouter(prefix="/api/v1", tags=["Profile"])

@router.get("/profile")
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

@router.put("/profile/username")
async def updateUsername(usernameDataInput: UpdateUsernameModel, currentUser: dict = Depends(get_current_user)):
    """Update username"""
    try: 
        result = await updateUsernameService (usernameDataInput, currentUser)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )
    
@router.put("/profile/password")
async def updatePassword(passwordDataInput: UpdatePasswordModel, currentUser: dict = Depends(get_current_user)):
    """Update password"""
    try:
        result = await updatePasswordService(passwordDataInput, currentUser)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )
    
@router.put("/profile/phone-number")
async def updatePhoneNumber(phoneDataInput: updatePhoneNumberModel, currentUser: dict = Depends(get_current_user)):
    """Update phone number"""
    try:
        result = await updatePhoneNumberService(phoneDataInput, currentUser)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )
    

@router.put("/profile/picture")
async def updateProfilePicture(
    profilePicture : UploadFile = File (...), 
    currentUser: dict = Depends(get_current_user)):
    """Update profile picture"""
    try : 
        result = await updateProfilePictureService(profilePicture, currentUser)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )