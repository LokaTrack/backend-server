from fastapi import FastAPI, HTTPException
from app.routers import authRouter, packageRouter, deliveryRouter, profileRouter, userRouter, testRouter
from app.services.mqttService import initialize_mqtt, stop_mqtt
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)


from app.utils.error import (
    validation_exception_handler, 
    http_exception_handler,
    general_exception_handler,
    not_found_exception_handler,
    method_not_allowed_exception_handler
)

app = FastAPI(
    title="Lokatani GPS Tracking API",
    docs_url="/api/v1/lokatrack/dokumentasi",
    openapi_url="/api/v1/lokatrack/openapi.json"  
)

# Include routers
app.include_router(authRouter.router)
app.include_router(packageRouter.router)
app.include_router(deliveryRouter.router)
app.include_router(profileRouter.router)
app.include_router(userRouter.router)
app.include_router(testRouter.router)
  
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(404, not_found_exception_handler)
app.add_exception_handler(405, method_not_allowed_exception_handler)

@app.on_event("startup")
def startup_mqtt_client():
    """Start MQTT client when FastAPI app starts"""
    logger.info("Starting MQTT location tracking...")
    initialize_mqtt()

@app.on_event("shutdown")
def shutdown_mqtt_client():
    """Stop MQTT client when FastAPI app shuts down"""
    logger.info("Stopping MQTT client...")
    stop_mqtt()

@app.get("/api/v1", tags=["Root"])
async def root():
    return {
        "status": "success", 
        "message": "Selamat datang di LokaTrack API"
    }