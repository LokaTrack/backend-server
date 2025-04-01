import requests
import logging
import os
from dotenv import load_dotenv
from datetime import datetime

logger = logging.getLogger(__name__)
load_dotenv()

MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN", "lokatrack.me")
EMAIL_FROM = os.getenv("EMAIL_FROM", "no-reply@lokatrack.me")

def sendEmail(to_email, subject, html_content, text_content=None):
    """
    Send email using Mailgun API
    """
    if not MAILGUN_API_KEY:
        logger.error("MAILGUN_API_KEY not set in environment variables")
        raise ValueError("MAILGUN_API_KEY not set")
    
    if not text_content:
        # Strip HTML tags for text version if not provided
        text_content = html_content.replace('<br>', '\n').replace('</p>', '\n\n')
        import re
        text_content = re.sub('<[^<]+?>', '', text_content)
    
    try:
        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            data={
                "from": f"LokaTrack <{EMAIL_FROM}>",
                "to": to_email,
                "subject": subject,
                "text": text_content,
                "html": html_content
            }
        )
        
        response.raise_for_status()  # Raise exception for 4XX/5XX errors
        return {"status": "success", "message_id": response.json().get("id")}
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send email: {str(e)}")
        return {"status": "error", "message": str(e)}