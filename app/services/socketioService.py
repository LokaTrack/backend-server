import socketio
import logging

logger = logging.getLogger(__name__)

# Create a Socket.IO server instance
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")