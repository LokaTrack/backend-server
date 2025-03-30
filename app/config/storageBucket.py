import logging
from google.cloud import storage
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

bucket_name = os.getenv("GCS_BUCKET_NAME")
if not bucket_name:
    logger.warning("GCS_BUCKET_NAME environment variable not set")
    storage_client = None  
else:
    storage_client = None
    try:
        # Step 1: Try using IAM role (Application Default Credentials)
        try:
            logger.info("Attempting to connect using IAM...")
            if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
                temp_cred_path = os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS")
            else:
                temp_cred_path = None

            storage_client = storage.Client()
            logger.info("Successfully connected to Cloud Storage using IAM")

        except Exception as iam_error:
            logger.warning(f"IAM connection failed: {str(iam_error)}")
            if temp_cred_path:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_cred_path

            # Step 2: Try using service account credentials
            logger.info("Attempting to connect using service account...")
            if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                try:
                    storage_client = storage.Client()
                    logger.info("Successfully connected to Cloud Storage using service account")

                except Exception as sa_error:
                    logger.error(f"Service account connection failed: {str(sa_error)}")
                    storage_client = None
            else:
                logger.error("No service account credentials available")
                storage_client = None

    except Exception as e:
        logger.critical(f"Cloud Storage initialization failed: {str(e)}")
        storage_client = None

# check if storage connection is successful
if storage_client is None:
    logger.warning("Cloud Storage client is None, continuing execution without cloud storage.")
else:
    logger.info("Cloud Storage configuration complete")
