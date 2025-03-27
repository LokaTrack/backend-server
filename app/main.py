from fastapi import FastAPI
from app.routers import authRouter, packageRouter, deliveryRouter

app = FastAPI (title= "Lokatani GPS Tracking API")

# Initialize Firestore on startup
# @app.on_event("startup")
# async def startup_db_client():
#     initializeFirestore()

# Include routers
app.include_router(authRouter.router)
app.include_router(packageRouter.router)
app.include_router(deliveryRouter.router)

@app.get("/", tags=["Root"])
async def root():
    return {
        "status": "success", 
        "message": "Selamat datang di LokaTrack API"
    }