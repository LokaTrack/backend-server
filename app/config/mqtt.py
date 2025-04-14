import ssl
import logging
import os
from paho.mqtt import client as mqtt_client
from paho.mqtt.client import Client
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_TOPIC = os.getenv("MQTT_TOPIC")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

mqtt_client_instance = None

def mqttConfig(callback_function=None):
    """Get or create MQTT client singleton"""
    global mqtt_client_instance
    
    if mqtt_client_instance is not None:
        return mqtt_client_instance
    
    client = Client(client_id=MQTT_CLIENT_ID, clean_session=True)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS) # Set up SSL/TLS for secure connection
    client.tls_insecure_set(False)
    
    # Register the provided callback function for messages
    if callback_function:
        client.on_message = callback_function
    
    # Set default connect callback
    client.on_connect = on_connect
    mqtt_client_instance = client
    
    return client

def on_connect(client, userdata, flags, rc):
    """Default connection callback"""
    if rc == 0:
        logger.info("Connected to MQTT Broker!")
        # Subscribe to the GPS topic
        client.subscribe(MQTT_TOPIC, qos=0)
        # (<MQTTErrorCode.MQTT_ERR_SUCCESS: 0>, 1)
    else:
        logger.error(f"Failed to connect to MQTT Broker, return code {rc}")


def connect_mqtt_client():
    """Connect the MQTT client to the broker"""
    client = mqtt_client_instance
    if not client:
        logger.error("MQTT client not initialized")
        return False
    try:
        client.connect(MQTT_BROKER, MQTT_PORT)
        # <MQTTErrorCode.MQTT_ERR_SUCCESS: 0> -> success
        # MQTT_ERR_NO_CONN: Client tidak dapat terhubung ke broker.
        # MQTT_ERR_INVAL: Parameter yang diberikan ke fungsi connect() tidak valid.
        # MQTT_ERR_CONN_REFUSED: Broker menolak koneksi (ex: karena kredensial salah).
        return True
    except Exception as e:
        logger.error(f"MQTT connection error: {str(e)}")
        return False
    
