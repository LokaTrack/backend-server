from fastapi import FastAPI, HTTPException
from app.routers import authRouter, packageRouter, deliveryRouter, profileRouter
from fastapi.exceptions import RequestValidationError
from app.utils.error import (
    validation_exception_handler, 
    http_exception_handler,
    general_exception_handler
)

app = FastAPI (title= "Lokatani GPS Tracking API")

# Initialize Firestore on startup
# @app.on_event("startup")
# async def startup_db_client():
#     initializeFirestore()

# Include routers
app.include_router(authRouter.router)
app.include_router(packageRouter.router)
app.include_router(deliveryRouter.router)
app.include_router(profileRouter.router)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


@app.get("/", tags=["Root"])
async def root():
    return {
        "status": "success", 
        "message": "Selamat datang di LokaTrack API"
    }