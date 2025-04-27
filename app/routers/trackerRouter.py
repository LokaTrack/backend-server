from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.utils.auth import get_current_user
from app.services.mqttService import process_gps_data
from app.models.mqttModel import GPSDataModel
from app.config.firestore import db
from google.cloud.firestore import FieldFilter
from typing import List, Dict
from app.services.trackerService import getTrackerLocation, getAllTracker, getTrackerDailyHistory

router = APIRouter(prefix="/api/v1", tags=["GPS Tracker"])

@router.get("/trackers/{trackerId}")
async def get_tracker_location(trackerId: str, currentUser: dict = Depends(get_current_user)):
    """Get info and latest location of a specific tracker"""
    try:    
        result = await getTrackerLocation(trackerId, currentUser)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )

@router.get("/trackers")
async def get_all_trackers(currentUser: dict = Depends(get_current_user)):
    """Get all trackers"""
    try:    
        result = await getAllTracker(currentUser)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )
    
@router.get("/trackers/{trackerId}/history")
async def get_tracker_daily_history(trackerId: str, currentUser: dict = Depends(get_current_user)):
    """Get today's location history for a specific tracker"""
    try:    
        result = await getTrackerDailyHistory(trackerId, currentUser)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )