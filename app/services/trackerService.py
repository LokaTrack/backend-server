from app.config.firestore import db
from app.models.authModel import EmailVerificationModel
from app.utils.security import getPasswordHash, verifyPassword
from app.utils.storeImage import uploadImageToStorage, uploadBytesToStorage
from app.utils.emailVerification import sendVerificationEmail
from app.utils.compress import compress_image
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
        tracker_doc = db.collection("trackerCollection").document(trackerId).get()
        
        if not tracker_doc.exists:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "fail",
                    "message": f"Tracker dengan id '{trackerId}' tidak ditemukan.",
                }
            )
        
        tracker_data = tracker_doc.to_dict()
        
        return {
            "status": "success",
            "message": "Berhasil mendapatkan data lokasi tracker",
            "data": tracker_data
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
        
        trackers = [doc.to_dict() for doc in trackers_docs]
        
        return {
            "status": "success",
            "message": "Berhasil mendapatkan data semua tracker",
            "data": trackers
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