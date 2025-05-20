import logging
import json
import os
import ssl
import paho.mqtt.client as mqtt
import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv
from app.models.mqttModel import GPSDataModel
from app.services.mqttService import process_gps_data
from app.utils.decrypt import decrypt_message
from app.utils.time import get_ntp_time, get_accurate_time
from app.config.sqlite import store_gps_data

# Global variable to store socketio instance
socketio_instance = None

def set_socketio(sio):
    """Set the Socket.IO instance to be used by MQTT module"""
    global socketio_instance
    socketio_instance = sio
    
# Helper function to run async emit in background
def emit_socketio_event(event, data):
    """Run socketio emit in an async context"""
    if not socketio_instance:
        logger.warning("Socket.IO not initialized, can't emit event")
        return
        
    # Create a new event loop for this thread if needed
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Create a coroutine to emit the event
    async def _emit():
        try:
            await socketio_instance.emit(event, data)
        except Exception as e:
            logger.error(f"Error emitting Socket.IO event: {str(e)}")
    
    # Run the coroutine in the event loop
    if loop.is_running():
        # If the loop is already running, we need to use create_task
        asyncio.run_coroutine_threadsafe(_emit(), loop)
    else:
        # Otherwise, we can just run it directly
        loop.run_until_complete(_emit())

# Configure logging
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "u7015b42.ala.asia-southeast1.emqxsl.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", 8883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "lokatrack/gps")
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "lokatrack-gps-1")
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "lokatrack-gps-1")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_SECURE = os.getenv("MQTT_TLS", "true").lower()

# MQTT client instance
mqtt_client = None


# Callback when the client receives a CONNACK response from the server
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT broker successfully")
        # Subscribe to the topic upon successful connection
        client.subscribe(MQTT_TOPIC)
        logger.info(f"Subscribed to topic: {MQTT_TOPIC}")
    else:
        logger.error(f"Failed to connect to MQTT broker with code {rc}")


# Callback when a message is received from the server
def on_message(client, userdata, msg):
    try:
        # logger.debug(f"Received message on topic '{msg.topic}': {msg.payload}")
        # receive_time = get_ntp_time()
        receive_time = get_accurate_time()

        # Decode the message payload
        data = decrypt_message(msg.payload.decode("utf-8"))

        # payload = msg.payload.decode("utf-8")
        # logger.info(f"Raw payload: {msg.payload}")
        # b'{\n  "id": "CC:DB:A7:9B:7A:00",\n  "lat": -6.2088,\n  "long": 106.8456\n}'

        # Parse the JSON data
        # data = json.loads(payload)
        # logger.info(f"data: {payload}")
        # {
        #   "id": "CC:DB:A7:9B:7A:00",
        #   "lat": -6.2088,
        #   "long": 106.8456
        #   "timestamp": "2025-05-14T04:44:49.351Z"
        # }

        latency_ms = None
        send_time = None

        # Jika ada timestamp di pesan, hitung latency
        if "timestamp" in data:
            try:
                # Parse timestamp dari pesan
                send_time = datetime.fromisoformat(data["timestamp"])
                logger.debug(
                    "---------------------------------------------------------------------------"
                )
                logger.debug(f"Current Time\t: {receive_time} ")
                logger.debug(f"Device time\t\t: {send_time} ")
                # Hitung latency dalam milidetik
                latency_ms = (receive_time - send_time).total_seconds() * 1000
                logger.debug(
                    f"MQTT Latency\t: {latency_ms:.2f}ms for message from {data.get('id', 'unknown')}"
                )
                logger.debug(
                    "---------------------------------------------------------------------------"
                )
            except (ValueError, KeyError) as e:
                logger.warning(f"Could not calculate latency: {e}")  

        # send via web socket
        # sio.emit("tracker:location_update", gps_data.dict(), room=gps_data.trackerId)
        store_gps_data(
            tracker_id=data.get("id"),
            latitude=data.get("lat"),
            longitude=data.get("long"),
            receive_time=receive_time,
            send_time=send_time,
            latency_ms=latency_ms
        )
        gps_data = GPSDataModel(**data)

        websocket_data = {
            "trackerId": gps_data.id,
            "location": {
                "latitude": gps_data.lat,
                "longitude": gps_data.long,
            },
            "timestamp": gps_data.timestamp,
        }
        # Use the global socketio instance via our helper function
        emit_socketio_event("tracker:location_update", websocket_data)

        # Process the GPS data (update Firestore)
        process_gps_data(gps_data)
        # For demonstration, we will just log the data

    # except Exception as e:
    #     logger.error(f"Error processing MQTT message: {str(e)}")
    except Exception as e:
        # Get exception type name
        error_type = type(e).__name__
        
        # Handle different types of errors differently
        if "ValidationError" in error_type:
            # For Pydantic validation errors, show exactly which fields failed
            error_details = str(e).split("\n")[1:3]  # Take just the key parts
            logger.error(f"MQTT data validation failed: {' | '.join(error_details)}")
            
            # Log the received data for debugging (optional)
            try:
                logger.debug(f"Invalid data received from tracker: {data.get('id', 'unknown')}")
            except:
                pass
                
        elif "KeyError" in error_type:
            # For missing keys
            logger.error(f"Missing required field in MQTT message: {str(e)}")
            
        elif "JSONDecodeError" in error_type:
            # For JSON parsing errors
            logger.error(f"Invalid JSON format in MQTT message")
            
        elif "AttributeError" in error_type:
            # For attribute errors (typically when trying to access attributes of None)
            logger.error(f"MQTT processing error: Unexpected data structure")
            
        else:
            # For other errors, provide a cleaner message
            logger.error(f"MQTT processing error ({error_type}): {str(e)[:100]}")
        
        # For debugging, you can log the full error to debug level
        logger.debug(f"Full error details: {str(e)}")
    

# Callback when client disconnects
def on_disconnect(client, userdata, rc):
    if rc != 0:
        logger.warning(f"Unexpected disconnection from MQTT broker with code {rc}")
    else:
        logger.info("Disconnected from MQTT broker")


def clear_retained_messages():
    """Clear retained messages on the topic"""
    try:
        client = get_mqtt_client()
        client.publish(MQTT_TOPIC, payload="", qos=0, retain=True)
        logger.info(f"Cleared retained messages on topic: {MQTT_TOPIC}")
        return True
    except Exception as e:
        logger.error(f"Error clearing retained messages: {str(e)}")
        return False


def setup_mqtt_client():
    """Initialize and configure the MQTT client"""
    global mqtt_client

    # # Create new MQTT client instance
    # mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_ID)

    # Create new MQTT client instance with protocol v311
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)

    # Enable automatic reconnection with backoff
    mqtt_client.reconnect_delay_set(min_delay=1, max_delay=30)

    # Set authentication
    if MQTT_USERNAME and MQTT_PASSWORD:
        mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    logger.debug(f"MQTT Secure is {MQTT_SECURE}")
    if MQTT_SECURE == "true":
        # Setup TLS for secure connection
        mqtt_client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)
        # mqtt_client.tls_insecure_set(True)

    # Set callbacks
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.on_disconnect = on_disconnect

    # Return the configured client
    return mqtt_client


def get_mqtt_client():
    """Get the MQTT client, creating it if it doesn't exist"""
    global mqtt_client
    if mqtt_client is None:
        mqtt_client = setup_mqtt_client()
    return mqtt_client


def start_mqtt_client():
    """Start the MQTT client and connect to broker"""
    try:
        client = get_mqtt_client()

        # Connect to the broker
        logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=120)

        # Start the loop in a background thread
        client.loop_start()
        logger.info("MQTT client started successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to start MQTT client: {str(e)}")
        return False


def stop_mqtt_client():
    """Stop the MQTT client properly"""
    global mqtt_client
    if mqtt_client:
        try:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
            logger.info("MQTT client stopped")
        except Exception as e:
            logger.error(f"Error stopping MQTT client: {str(e)}")
