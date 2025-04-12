from datetime import datetime
from app.config.storageBucket import storage_client
from app.utils.error import HTTPException
import os
from dotenv import load_dotenv

load_dotenv()


async def uploadImageToStorage(file, location, fileName):
    """Upload image to Google Cloud Storage"""
    try:
        bucket = storage_client.bucket(os.getenv("GCS_BUCKET_NAME"))
        blob = bucket.blob(f"{location}/{fileName}")
        blob.upload_from_file(file.file, content_type=file.content_type)
        blob.make_public()
        url = blob.public_url
        
        return url
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )
    
async def uploadBytesToStorage(bytes, location, fileName, content_type):
    """Upload image to Google Cloud Storage"""
    try:
        bucket = storage_client.bucket(os.getenv("GCS_BUCKET_NAME"))
        blob = bucket.blob(f"{location}/{fileName}")
        blob.upload_from_string (data= bytes, 
                                 content_type= content_type)
        blob.make_public()
        url = blob.public_url
        
        return url
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )    