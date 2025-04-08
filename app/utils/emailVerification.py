from app.utils.email import sendEmail
from app.utils.template import renderTemplate
from fastapi import HTTPException
import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()
APP_DOMAIN = os.getenv("APP_DOMAIN", "https://lokatrack.me")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://lokatrack.me")
MOBILE_APP_URL = os.getenv("MOBILE_APP_URL", "https://lokatrack.me/app/open")

async def sendVerificationEmail (email: str, username:str, emailVerificationToken: str) : 
    """Send Email Verification"""
    try :
        # generate verification link
        verification_url = f"{APP_DOMAIN}/verify-email/{emailVerificationToken}"

        html_content = renderTemplate(
            "account_verification_email.html",
            username=username,
            verification_url=verification_url
        )
        email_result = sendEmail(
            to_email=email,
            subject="Verifikasi Email LokaTrack",
            html_content=html_content
        )
        
        if email_result["status"] == "error":
            logger.error(f"Failed to send verification email: {email_result['message']}")
            # Continue execution even if email sending fails
        
        return {
            "status": "success", 
            "message": "Verification email sent"
            }
    
    except Exception as e:
        logger.error(f"Error sending verification email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Server Error while sending verification email: {str(e)}"
        )