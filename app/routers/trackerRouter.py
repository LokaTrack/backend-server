from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.utils.auth import get_current_user
from app.services.trackerService import getTrackerLocation
from app.services.mqttService import get_last_location, get_all_last_locations
from app.config.mqtt import mqtt_client_instance, MQTT_TOPIC
from datetime import datetime

router = APIRouter(prefix="/api/v1", tags=["Tracker"])

@router.get("/tracker/{trackerId}", status_code=200)
async def get_tracker_location(trackerId: str, currentUser: dict = Depends(get_current_user)):
    """Get latest tracker location"""
    try:
        result = await getTrackerLocation(trackerId)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )

@router.get("/mqtt/status", status_code=200)
async def get_mqtt_status(currentUser: dict = Depends(get_current_user)):
    """Get MQTT connection status and last received locations"""
    if currentUser["role"] != "admin":
        return JSONResponse(
            status_code=403,
            content={
                "status": "fail",
                "message": "Anda tidak memiliki akses untuk melihat status MQTT",
                "timestamp": datetime.now().isoformat()
            }
        )
    
    locations = get_all_last_locations()
    return {
        "status": "success",
        "message": "MQTT status",
        "data": {
            "connected": bool(locations),  # If we have any locations, we are connected
            "trackerCount": len(locations),
            "lastLocations": locations
        }
    }

@router.get("/mqtt/debug", status_code=200)
async def get_mqtt_debug():
    """Get detailed MQTT debug info (no auth for troubleshooting)"""
    
    # Safer way to check connection status
    is_connected = False
    client_id = None
    
    if mqtt_client_instance:
        # Use is_connected() method instead of accessing private attribute
        try:
            is_connected = mqtt_client_instance.is_connected()
        except:
            # Fall back to checking if we have received any locations
            is_connected = len(get_all_last_locations()) > 0
            
        # Safely get client_id
        try:
            if hasattr(mqtt_client_instance, '_client_id'):
                client_id = mqtt_client_instance._client_id.decode()
            else:
                client_id = mqtt_client_instance._client_id_
        except:
            client_id = "Unknown (unable to retrieve)"
    
    return {
        "status": "success",
        "message": "MQTT debug info",
        "data": {
            "mqtt_client": {
                "connected": is_connected,
                "client_id": client_id,
                "subscribed_topic": MQTT_TOPIC
            },
            "last_locations_count": len(get_all_last_locations()),
            "last_locations": get_all_last_locations()
        }
    }