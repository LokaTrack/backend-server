import logging
from datetime import datetime, timezone
from google.cloud import firestore
from app.config.firestore import db
from app.models.mqttModel import GPSDataModel
from uuid_utils import uuid7

# Configure logging
logger = logging.getLogger(__name__)

# async def process_gps_data(gps_data: GPSDataModel):
#     """Process GPS data received from MQTT and update Firestore"""
#     try:
#         if not db:
#             logger.error("Firestore database not initialized")
#             return False

#         trackerId = gps_data.id
#         geopoint = firestore.GeoPoint(gps_data.lat, gps_data.long)
#         timestamp = datetime.fromisoformat(gps_data.timestamp)

#         locationData = {
#             # "location": {
#             #     "latitude": gps_data.lat,
#             #     "longitude": gps_data.long
#             # },
#             "location": geopoint,
#             "lastUpdate": timestamp,
#         }

#         # Update the tracker document in Firestore
#         trackerRef = db.collection("trackerCollection").document(trackerId)

#         # Check if the tracker document exists
#         trackerDoc = trackerRef.get()

#         batch = db.batch()

#         if trackerDoc.exists:
#             # Update existing tracker document
#             batch.update(trackerRef, locationData)
#             # trackerRef.update(locationData)
#             logger.debug(f"Updated location for tracker {trackerId}")
#         else:
#             # Create new tracker document with basic info
#             tracker_data = {
#                 "trackerId": trackerId,
#                 "trackerName": f"GPS Tracker {trackerId}",
#                 "registrationDate": datetime.now(timezone.utc),
#                 **locationData,
#             }
#             batch.set(trackerRef, tracker_data)
#             # trackerRef.set(tracker_data)
#             logger.debug(f"Created new tracker record for {trackerId}")

#         # save location to history
#         # Create document with auto-generated ID in history subcollection
#         historyData = {"location": geopoint, "timestamp": timestamp}

#         historyId = str(uuid7())

#         # save location to history
#         historyRef = trackerRef.collection("locationHistory").document(historyId)
#         # historyRef.set(locationHistory)
#         batch.set(historyRef, historyData)

#         # Commit all changes
#         batch.commit()
#         return True
#     except Exception as e:
#         logger.error(f"Error updating tracker location: {str(e)}")
#         return False


def process_gps_data(gps_data: GPSDataModel):
    """Non-async version for direct use in MQTT callbacks"""
    try:
        if not db:
            logger.error("Firestore database not initialized")
            return False

        trackerId = gps_data.id
        geopoint = firestore.GeoPoint(gps_data.lat, gps_data.long)
        # timestamp = datetime.fromisoformat(gps_data.timestamp)

        # Handle timestamp with 'Z' suffix properly
        timestamp_str = gps_data.timestamp
        if timestamp_str.endswith('Z'):
            # Replace Z with +00:00 (UTC)
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            timestamp = datetime.fromisoformat(timestamp_str)


        # Prepare location data for Firestore
        locationData = {
            # "location": {
            #     "latitude": gps_data.lat,
            #     "longitude": gps_data.long
            # },
            "location": geopoint,
            "lastUpdate": timestamp,
        }
        # Update the tracker document in Firestore
        trackerRef = db.collection("trackerCollection").document(trackerId)

        # Check if the tracker document exists
        trackerDoc = trackerRef.get()

        # Start a batch write
        batch = db.batch()

        if trackerDoc.exists:
            # Update existing tracker document
            batch.update(trackerRef, locationData)
            # trackerRef.update(locationData)
            logger.debug(f"Updated location for tracker {trackerId}")
        else:
            # Create new tracker document with basic info
            tracker_data = {
                "trackerId": trackerId,
                "trackerName": f"GPS Tracker {trackerId}",
                "registrationDate": datetime.now(timezone.utc),
                **locationData,
            }
            batch.set(trackerRef, tracker_data)
            # trackerRef.set(tracker_data)
            logger.debug(f"Created new tracker record for {trackerId}")

        historyData = {"location": geopoint, "timestamp": timestamp}

        # Generate UUIDv7 (timestamp-based)
        historyId = str(uuid7())

        # save location to history
        historyRef = trackerRef.collection("locationHistory").document(historyId)
        # historyRef.set(locationHistory)
        batch.set(historyRef, historyData)

        # Commit all changes
        batch.commit()

        return True

    except Exception as e:
        logger.error(f"Error updating tracker location: {str(e)}")
        return False
