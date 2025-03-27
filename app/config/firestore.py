import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

try:
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        # Check if GOOGLE_APPLICATION_CREDENTIALS is a JSON string
        try:
            credentials_data = json.loads(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
            print("[✅] Using GOOGLE_APPLICATION_CREDENTIALS as JSON")
            cred = credentials.Certificate(credentials_data)
        except json.JSONDecodeError:
            # If not JSON, assume it's a file path
            print("[✅] Using GOOGLE_APPLICATION_CREDENTIALS as file path")
            cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
    else:
        # If no credentials provided, use default application credentials (IAM role)
        print("-> Using IAM role")
        cred = credentials.ApplicationDefault()
    # Initialize Firebase app if not already initialized
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
        print("[✅] Firestore initialized successfully")
    # Return Firestore client
    db = firestore.client()

except Exception as e:
        print("[❌] Error initializing Firestore:", e)
        raise RuntimeError("[❌] Failed to initialize Firestore. Please check your configuration.")