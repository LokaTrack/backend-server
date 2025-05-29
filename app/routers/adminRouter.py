from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from app.utils.auth import get_current_user
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from app.services.adminService import (
    getAllUsers,
    assign_tracker_service,
    get_all_delivery_packages_service,
    get_admin_dashboard_service,
    getGPSData,
)
from app.config.sqlite import get_recent_gps_data
from typing import Optional

router = APIRouter(prefix="/api/v1/admin", tags=["Administrator"])

# @router.get(path="/users-2", status_code=200)
# async def get_all_users_1(currentUser: dict = Depends(get_current_user)):
#     """Get All Users"""
#     try:
#         result = await getAllUsers (currentUser)
#         return result
#     except HTTPException as e:
#         return JSONResponse(
#             status_code=e.status_code,
#             content=e.detail
#         )

@router.get("/dashboard", status_code=200)
async def get_admin_dashboard(
    currentUser: dict = Depends(get_current_user)
):
    """Get admin dashboard with overview statistics"""
    try:
        result = await get_admin_dashboard_service(currentUser)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )

@router.get("/users", status_code=200)
async def get_all_users(
    role: Optional[str] = Query(None, description="Filter by user role (pending, inactive, admin/driver)"),
    email_verified: Optional[bool] = Query(None, description="Filter by email verification status"),
    search: Optional[str] = Query(None, description="Search by username or email"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of users to return"),
    offset: int = Query(0, ge=0, description="Number of users to skip"),
    currentUser: dict = Depends(get_current_user)
):
    """Get all users with optional filtering"""
    try:
        result = await getAllUsers(
            role=role,
            email_verified=email_verified,
            search=search,
            limit=limit,
            offset=offset,
            currentUser=currentUser
        )
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )

@router.put("/trackers/{trackerId}", status_code=200)
async def assign_tracker(
    userId: str = Body(..., embed=True,description="User ID to assign tracker to"),
    trackerId: str = Path(..., description="Tracker ID to assign"),
    currentUser: dict = Depends(get_current_user)
):
    """Assign a tracker to a user"""
    try:
        result = await assign_tracker_service(userId=userId, trackerId=trackerId, currentUser=currentUser)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )

@router.get("/deliveries", status_code=200)
async def get_all_deliveries(
    status: Optional[str] = Query(None, description="Filter by delivery status"),
    driver_id: Optional[str] = Query(None, description="Filter by driver ID"),
    date_from: Optional[str] = Query(None, description="Filter by delivery start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter by delivery end date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    currentUser: dict = Depends(get_current_user)
):
    """Get all delivery packages with optional filtering"""
    try:
        result = await get_all_delivery_packages_service(
            status=status,
            driver_id=driver_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset,
            currentUser=currentUser
        )
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )

@router.get("/gps-data", status_code=200)
async def get_gps_data(
    trackerId: Optional[str] = Query(None, description="Filter by tracker ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    currentUser: dict = Depends(get_current_user)
):
    """Get recent GPS data from SQLite database"""
    try:      
        result = await getGPSData(trackerId, limit, currentUser)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )