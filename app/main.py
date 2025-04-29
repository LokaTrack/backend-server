import os
from fastapi import FastAPI, HTTPException
from app.config.logging import configure_logging
from fastapi import FastAPI, HTTPException
from app.routers import authRouter, packageRouter, deliveryRouter, profileRouter, userRouter, testRouter, trackerRouter, ocrRouter
from app.config.mqtt import start_mqtt_client, stop_mqtt_client, clear_retained_messages
from fastapi.exceptions import RequestValidationError
import uvicorn
import logging
from fastapi.middleware.cors import CORSMiddleware  

logger = logging.getLogger(__name__)

from app.utils.error import (
    validation_exception_handler, 
    http_exception_handler,
    general_exception_handler,
    not_found_exception_handler,
    method_not_allowed_exception_handler
)

log_level = os.getenv("LOG_LEVEL", "INFO")
configure_logging(log_level)

app = FastAPI(
    title="Lokatani GPS Tracking API",
    docs_url="/api/v1/lokatrack/dokumentasi",
    openapi_url="/api/v1/lokatrack/openapi.json"  
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# Include routers
app.include_router(authRouter.router)
app.include_router(packageRouter.router)
app.include_router(deliveryRouter.router)
app.include_router(profileRouter.router)
app.include_router(userRouter.router)
app.include_router(trackerRouter.router)
app.include_router(testRouter.router)
app.include_router(ocrRouter.router)
  
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(404, not_found_exception_handler)
app.add_exception_handler(405, method_not_allowed_exception_handler)

@app.get("/api/v1", tags=["Root"])
async def root():
    return {
        "status": "success", 
        "message": "Selamat datang di LokaTrack API"
    }

@app.on_event("startup")
async def startup_event():
    """Start MQTT client on application startup"""
    # Start the MQTT client
    start_mqtt_client()
    # Clear retained messages
    clear_retained_messages()    

@app.on_event("shutdown")
async def shutdown_event():
    """Stop MQTT client on application shutdown"""
    # Stop the MQTT client
    stop_mqtt_client()

if __name__ == "__main__" : 
    logger.debug("Starting FastAPI application, log level: %s", log_level)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level=log_level.lower())
# now you can run the app using the command:
# python -m app.main
# or using the command:
# uvicorn app.main:app --host 0.0.0.0 --port 8000