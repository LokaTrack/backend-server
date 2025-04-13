from app.config.firestore import db
from app.utils.time import convert_utc_to_wib
import logging
from fastapi import HTTPException
from datetime import datetime, timezone
from google.cloud import firestore


logger = logging.getLogger(__name__)

async def getTrackerLocation(trackerId):
    """Get the latest location of a tracker"""
    try:
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
                    "message": f"Tracker dengan ID '{trackerId}' tidak ditemukan.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        trackerData = trackerDoc.to_dict()
        
        # Convert timestamp to WIB if it exists
        if "lastUpdated" in trackerData:
            trackerData["lastUpdated"] = convert_utc_to_wib(trackerData["lastUpdated"])
        
        return {
            "status": "success",
            "message": "Berhasil mendapatkan lokasi tracker",
            "data": {
                "trackerId": trackerId,
                "trackerName": trackerData.get("trackerName"),
                "location": trackerData.get("location"),
                "lastUpdated": trackerData.get("lastUpdated")
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tracker location: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
def updateTrackerLocation(tracker_id, latitude, longitude, timestamp):
    """Update tracker location in Firestore"""
    try:
        # Check if tracker exists
        tracker_ref = db.collection("trackerCollection").document(tracker_id)
        tracker_doc = tracker_ref.get()
        
        if not tracker_doc.exists:
            logger.warning(f"Tracker {tracker_id} not found, creating new tracker document")
            # Create new tracker document
            tracker_ref.set({
                "trackerId": tracker_id,    
                "trackerName": f"GPS Tracker {tracker_id}",
                "registrationDate": timestamp,
                "location": firestore.GeoPoint(latitude, longitude),  # Gunakan GeoPoint
                "lastUpdated": timestamp
            })
            logger.info(f"Created new tracker {tracker_id} with initial location")
        else:
            # Update existing tracker
            tracker_ref.update({
                "location": firestore.GeoPoint(latitude, longitude),  # Gunakan GeoPoint
                "lastUpdated": timestamp
            })
            logger.info(f"Updated location for tracker {tracker_id}")
        
        return True
    except Exception as e:
        logger.error(f"Error updating tracker location: {str(e)}")
        return False


