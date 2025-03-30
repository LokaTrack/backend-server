import logging
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from dotenv import load_dotenv

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if not PROJECT_ID and not GOOGLE_APPLICATION_CREDENTIALS:
    logger.warning("PROJECT_ID or GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
    db = None  # Tetap lanjutkan tanpa Firestore
else:
    db = None

    try:
        # Step 1: Try using IAM role (Application Default Credentials)
        try:
            logger.info("Attempting to connect using IAM...")
            if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
                temp_cred_path = os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS")
            else:
                temp_cred_path = None

            cred = credentials.ApplicationDefault()

            if not firebase_admin._apps:
                app = firebase_admin.initialize_app(cred, {"projectId": PROJECT_ID})
            else:
                app = firebase_admin.get_app()

            db = firestore.client(app)
            logger.info(f"Successfully connected to Firestore using IAM for project: {PROJECT_ID}")

        except Exception as iam_error:
            logger.warning(f"IAM connection failed: {iam_error}")
            if temp_cred_path:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_cred_path

            # Step 2: Try using service account credentials
            logger.info("Attempting to connect using service account...")
            if GOOGLE_APPLICATION_CREDENTIALS:
                try:
                    try:
                        credentials_data = json.loads(GOOGLE_APPLICATION_CREDENTIALS)
                        cred = credentials.Certificate(credentials_data)
                        logger.info("Using credentials from JSON string")
                    except json.JSONDecodeError:
                        cred = credentials.Certificate(GOOGLE_APPLICATION_CREDENTIALS)
                        logger.info("Using credentials from file path")

                    if not firebase_admin._apps:
                        app = firebase_admin.initialize_app(cred, {"projectId": PROJECT_ID})
                    else:
                        app = firebase_admin.get_app()

                    db = firestore.client(app)
                    logger.info(f"Successfully connected to Firestore using service account for project: {PROJECT_ID}")

                except Exception as sa_error:
                    logger.error(f"Service account connection failed: {sa_error}")
                    db = None
            else:
                logger.error("No service account credentials available")
                db = None

    except Exception as e:
        logger.critical(f"Firestore initialization failed: {e}")
        db = None

# Cek apakah koneksi ke Firestore berhasil
if db is None:
    logger.warning("Firestore client is None, continuing execution without Firestore.")
else:
    logger.info("Firestore configuration complete")
