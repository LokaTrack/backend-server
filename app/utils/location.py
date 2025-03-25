from app.config.firestore import get_db
from fastapi import HTTPException
from datetime import datetime

async def getPackageLocation (trackerId: str):
    """Get the location of a package"""
    db = get_db()
    trackerDoc = db.collection("trackerCollection").document(trackerId).get()
    
    if not trackerDoc.exists:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "fail",
                "message": f"Tracker dengan ID '{trackerId}' tidak ditemukan.",
                "timestamp": datetime.now().isoformat()
            }
        )    

    tracker_data = trackerDoc.to_dict()
    
    location = {
        "latitude": tracker_data.get("latitude", 0.0),
        "longitude": tracker_data.get("longitude", 0.0),
    }
        
    return location