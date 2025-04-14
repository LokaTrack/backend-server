import logging
from datetime import datetime, timezone
from app.config.firestore import db
from app.models.mqttModel import GPSDataModel

# Configure logging
logger = logging.getLogger(__name__)

async def process_gps_data(gps_data: GPSDataModel):
    """Process GPS data received from MQTT and update Firestore"""
    try:
        if not db:
            logger.error("Firestore database not initialized")
            return False

        tracker_id = gps_data.id
        
        # Prepare location data for Firestore
        location_data = {
            "location": {
                "latitude": gps_data.lat,
                "longitude": gps_data.long
            },
            "lastUpdated": datetime.now(timezone.utc)
        }
        
        # Update the tracker document in Firestore
        tracker_ref = db.collection("trackerCollection").document(tracker_id)
        
        # Check if the tracker document exists
        tracker_doc = tracker_ref.get()
        
        if tracker_doc.exists:
            # Update existing tracker document
            tracker_ref.update(location_data)
            logger.info(f"Updated location for tracker {tracker_id}")
        else:
            # Create new tracker document with basic info
            tracker_data = {
                "trackerId": tracker_id,
                "trackerName": f"GPS Tracker {tracker_id}",
                "registrationDate": datetime.now(timezone.utc),
                **location_data
            }
            tracker_ref.set(tracker_data)
            logger.info(f"Created new tracker record for {tracker_id}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error updating tracker location: {str(e)}")
        return False

def process_gps_data(gps_data: GPSDataModel):
    """Non-async version for direct use in MQTT callbacks"""
    try:
        if not db:
            logger.error("Firestore database not initialized")
            return False

        tracker_id = gps_data.id
        
        # Prepare location data for Firestore
        location_data = {
            "location": {
                "latitude": gps_data.lat,
                "longitude": gps_data.long
            },
            "lastUpdated": datetime.now(timezone.utc)
        }
        
        # Update the tracker document in Firestore
        tracker_ref = db.collection("trackerCollection").document(tracker_id)
        
        # Check if the tracker document exists
        tracker_doc = tracker_ref.get()
        
        if tracker_doc.exists:
            # Update existing tracker document
            tracker_ref.update(location_data)
            logger.info(f"Updated location for tracker {tracker_id}")
        else:
            # Create new tracker document with basic info
            tracker_data = {
                "trackerId": tracker_id,
                "trackerName": f"GPS Tracker {tracker_id}",
                "registrationDate": datetime.now(timezone.utc),
                **location_data
            }
            tracker_ref.set(tracker_data)
            logger.info(f"Created new tracker record for {tracker_id}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error updating tracker location: {str(e)}")
        return False