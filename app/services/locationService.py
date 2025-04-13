import json
import logging
from datetime import datetime, timezone
from app.utils.time import convert_utc_to_wib
from app.config.firestore import db
from google.cloud import firestore
from app.config.mqtt import get_mqtt_client, connect_mqtt_client, MQTT_TOPIC

logger = logging.getLogger(__name__)

# Store the last received location for each tracker
last_locations = {}

def on_message(client, userdata, msg):
    """Process incoming MQTT location messages"""
    try:
        # Log the raw message and topic
        logger.info(f"MQTT message received on topic: {msg.topic}")
        # logger.info(f"Raw payload: {msg.payload}")
        # b'{\n  "id": "CC:DB:A7:9B:7A:00",\n  "lat": -6.2088,\n  "long": 106.8456\n}'
        
        # Decode and parse the message
        payload = msg.payload.decode()
        # logger.info(f"Decoded payload: {payload}")
        # {
        #   "id": "CC:DB:A7:9B:7A:00",
        #   "lat": -6.2088,
        #   "long": 106.8456
        # }
        
        data = json.loads(payload)
        logger.info(f"Parsed JSON data: {data}")
        # {'id': 'CC:DB:A7:9B:7A:00', 'lat': -6.2088, 'long': 106.8456} 
        
        # Check for required fields
        if "id" in data and "lat" in data and "long" in data:
            
            # Add current timestamp
            current_time = datetime.now(timezone.utc)
            
            # Store in memory for status checks
            data["timestamp"] = convert_utc_to_wib(current_time)
            last_locations[data["id"]] = data
            
            # Update tracker in Firestore
            success = update_tracker_location(data["id"], data["lat"], data["long"], current_time)
            # success = 'success'
            logger.info(f"Tracker location update result: {'Success' if success else 'Failed'}")
        else:
            logger.warning(f"Invalid GPS data format, missing required fields: {payload}")
    
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON: {payload}. Error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing MQTT message: {str(e)}", exc_info=True)

        
def update_tracker_location(tracker_id, latitude, longitude, timestamp):
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

def get_last_location(tracker_id):
    """Get the last known location for a tracker"""
    return last_locations.get(tracker_id)

def get_all_last_locations():
    """Get all last known locations"""
    return last_locations

def initialize_mqtt():
    """Initialize the MQTT client for location tracking"""
    client = get_mqtt_client(callback_function=on_message)
    success = connect_mqtt_client()
    
    if success:
        # Start the MQTT loop in a non-blocking way
        client.loop_start()
        logger.info("MQTT client started successfully")
        return True
    else:
        logger.error("Failed to start MQTT client")
        return False

def stop_mqtt():
    """Stop the MQTT client"""
    from app.config.mqtt import mqtt_client_instance
    if mqtt_client_instance:
        mqtt_client_instance.loop_stop()
        mqtt_client_instance.disconnect()
        logger.info("MQTT client disconnected")
        return True
    return False