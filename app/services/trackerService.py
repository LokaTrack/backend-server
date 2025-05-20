from app.config.firestore import db
from app.utils.time import convert_utc_to_wib, get_wib_day_range
from fastapi import HTTPException
from datetime import datetime, timezone
from google.cloud.firestore import FieldFilter
import logging
logger = logging.getLogger(__name__)


async def getTrackerLocation(trackerId, currentUser):
    """Get the latest location of a specific tracker"""
    try:
        # Check if user is authenticated
        if currentUser["role"] not in ["admin", "driver"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "status": "fail",
                    "message": "Anda tidak memiliki akses untuk melihat data tracker.",
                }
            )
        
        # Get tracker from database
        trackerDoc = (
            db.collection("trackerCollection")
            .document(trackerId)
            .get()
        )                
        
        if not trackerDoc.exists:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "fail",
                    "message": f"Tracker dengan id '{trackerId}' tidak ditemukan.",
                }
            )
        
        trackerData = trackerDoc.to_dict()
        data = {
            "trackerId": trackerData.get("trackerId"),
            "trackerName": trackerData.get("trackerName"),
            "location": trackerData.get("location"),
            "lastUpdate": trackerData.get("lastUpdate"),
            "registrationDate": trackerData.get("registrationDate"),        
        }
        
        # Get user who uses the tracker
        userDoc = (
            db.collection("userCollection")
            .where(filter = FieldFilter("trackerId", "==",trackerId))
            .limit(1)
            .get()
        )
        if userDoc:
            userData = userDoc[0].to_dict()

            # update tracker Data with user data
            data.update({
                "userId": userData.get("userId"),
                "username": userData.get("username"),
                "phoneNumber": userData.get("phoneNumber")
            })
        
        return {
            "status": "success",
            "message": "Berhasil mendapatkan data lokasi tracker",
            "data": data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
            }
        )

async def getTrackerDailyHistory(trackerId, currentUser):
    """Get today's location history for a specific tracker"""
    try:
        # Check if user is authenticated
        if currentUser["role"] not in ["admin", "driver"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "status": "fail",
                    "message": "Anda tidak memiliki akses untuk melihat history tracker.",
                }
            )
        
        # Get range for today in WIB timezone
        todayStart, todayEnd = get_wib_day_range()
        
        # Get tracker from database to verify it exists
        trackerRef = db.collection("trackerCollection").document(trackerId)
        trackerDoc = trackerRef.get()
                
        if not trackerDoc.exists:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "fail",
                    "message": f"Tracker dengan id '{trackerId}' tidak ditemukan.",
                }
            )
        
        trackerData = trackerDoc.to_dict()
        
        # Get location history from subcollection for today
        historyQuery = (
            trackerRef.collection("locationHistory")
            .where(filter=FieldFilter("timestamp", ">=", todayStart))
            .where(filter=FieldFilter("timestamp", "<=", todayEnd))
            .order_by("timestamp", direction="DESCENDING")
        )
        
        # Execute query
        historyDocs = historyQuery.stream()
        
        # Process results
        historyLocations = []
        for doc in historyDocs:                                                                                                                                                                                                                                                                                                                                                                                                                             
            locationData = doc.to_dict()
            historyData = {}
            # # Format GeoPoint for JSON response
            # if "location" in locationData and locationData["location"]:
            #     locationData["location"] = {
            #         "latitude": locationData["location"].latitude,
            #         "longitude": locationData["location"].longitude
            #     }
            historyData["latitude"] = locationData["location"].latitude
            historyData["longitude"] = locationData["location"].longitude

            # Convert timestamp to WIB
            if "timestamp" in locationData and locationData["timestamp"]:
                historyData["timestamp"] = convert_utc_to_wib(locationData["timestamp"]).isoformat()
            
            historyLocations.append(historyData)
        
        data = {
            "trackerId": trackerId,
            "trackerName": trackerData.get("trackerName"),
            "date": todayStart.strftime("%Y-%m-%d"),
            "totalLocations": len(historyLocations),
            "history": historyLocations
        }
        
        return {
            "status": "success",
            "message": "Berhasil mendapatkan history lokasi tracker hari ini",
            "data": data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tracker daily history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
            }
        )

async def getAllTracker(currentUser):
    """Get all trackers"""
    try:
        # Check if user is admin
        if currentUser["role"] not in ["admin"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "status": "fail",
                    "message": "Anda tidak memiliki akses untuk melihat semua data tracker.",
                }
            )
        
        # Get all trackers
        trackers_docs = db.collection("trackerCollection").stream()
        
        trackerList = []
        # trackers = [doc.to_dict() for doc in trackers_docs]
        for tracker in trackers_docs: 
            trackerDict = tracker.to_dict()
            trackerData = {
                "trackerId" : trackerDict.get("trackerId"),
                "trackerData" : trackerDict
            }
            
            trackerList.append(trackerData)
        
        return {
            "status": "success",
            "message": "Berhasil mendapatkan data semua tracker",
            "data": trackerList
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
            }
        )