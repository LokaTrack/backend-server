from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from app.models.userModel import UpdatePasswordModel, updatePhoneNumberModel, UpdateUsernameModel
from app.utils.auth import get_current_user
from app.services.userService import getDashboard

router = APIRouter(prefix="/api/v1", tags=["User Application"])

@router.get("/dashboard")
async def getDashboardData(currentUser: dict = Depends(get_current_user)):
    """Get user data"""
    try:    
        print("try to get dashboard")
        result = await getDashboard(currentUser)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )
    
