from app.config.firestore import db
from app.models.userModel import UserModel
from app.models.authModel import OtpVerificationModel, EmailVerificationModel
from app.utils.security import getPasswordHash, verifyPassword, createAccessToken
from app.utils.email import sendEmail
from app.utils.template import renderTemplate
from app.utils.time import convert_utc_to_wib
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from datetime import datetime, timezone
from google.cloud.firestore import FieldFilter, DELETE_FIELD
import logging
import os
import uuid
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()
APP_DOMAIN = os.getenv("APP_DOMAIN", "https://lokatrack.me")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://lokatrack.me")
MOBILE_APP_URL = os.getenv("MOBILE_APP_URL", "https://lokatrack.me/app/open")


async def registerUser(userDataInput):
    """Register a new user"""
    try : 
        # Check if email already exists
        docUsers = (
            db.collection("userCollection")   
            .where(filter=FieldFilter("email", "==", userDataInput.email))
            .limit(1)
            .get()
        )
        # Check password length
        if len (userDataInput.password) < 8 :
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "Password harus memiliki minimal 8 karakter",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        # Check if password and password confirmation match
        if userDataInput.password != userDataInput.passwordConfirmation: 
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "Password dan password konfirmasi tidak sama",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        if len(docUsers) > 0:
            userData = docUsers[0].to_dict()
            # Check is email verified
            if userData.get("isEmailVerified"):
                raise HTTPException(
                    status_code=409,  
                    detail={
                        "status": "fail",
                        "message": "Email ini sudah digunakan",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
            # check count resend verification email
            if userData.get("countResendVerificationEmail") >= 3:
                raise HTTPException(
                    status_code=409,  
                    detail={
                        "status": "fail",
                        "message": "Anda terlalu banyak meminta verifikasi email! Mohon hubungi administrator",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
            
            verificationData = EmailVerificationModel.generate()
            # send email 
            await sendVerificationEmail(
                email=userDataInput.email,
                username=userDataInput.username,
                emailVerificationToken = verificationData.emailVerificationToken
            )

            db.collection("userCollection").document(userData("userId")).update({
                "emailVerificationToken": verificationData.emailVerificationToken,
                "emailVerificationTokenExpiry": verificationData.emailVerificationTokenExpiry,
                "lastUpdate": datetime.now(timezone.utc),
                "countResendVerificationEmail": userData.get("countResendVerificationEmail", 0) + 1
            })
            return {
                "status": "success",
                "message": "Email verifikasi telah dikirim! Silahkan cek email anda untuk aktivasi akun"
            }

        # Create new user
        newUserData = UserModel(
            email=userDataInput.email,
            username=userDataInput.username,
            hashedPassword=getPasswordHash(userDataInput.password),
        )

        # Generate email verification token
        verificationData = EmailVerificationModel.generate()
        newUserDataInDict = newUserData.dict()
        newUserDataInDict.update({
            "emailVerificationToken": verificationData.emailVerificationToken,
            "emailVerificationTokenExpiry": verificationData.emailVerificationTokenExpiry,
            "countResendVerificationEmail": 0,
        })

        # Save user to Firestore
        db.collection("userCollection").document(newUserDataInDict.get("userId")).set(newUserDataInDict)

        # Send verification email
        try:
            await sendVerificationEmail(
                email=userDataInput.email, 
                username=userDataInput.username, 
                emailVerificationToken = verificationData.emailVerificationToken
            )
        except Exception as email_error:
            logger.error(f"Error sending verification email: {str(email_error)}")

        return {
            "status": "success",
            "message": "Akun anda berhasil dibuat! Silahkan cek email untuk aktivasi akun"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error while registering user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan pada server: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

async def loginUser(userDataInput):
    """Authenticate a user and return a token"""
    try : 
        # Find user by email
        userDocs = (
        db.collection("userCollection")
        .where(filter=FieldFilter("email", "==", userDataInput.email))
        .limit(1)
        .get()
        )
        #[
        #   <google.cloud.firestore_v1.document.DocumentSnapshot object at 0x7f1234567890> -> snapshot
        #]
        if len(userDocs) == 0:
            raise HTTPException(
                status_code=401,
                detail={
                    "status": "fail",
                    "message": "Email atau password salah",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

        userDoc = userDocs[0]
        # <google.cloud.firestore_v1.document.DocumentSnapshot object at 0x7f1234567890>

        userDataDB = userDoc.to_dict()
        # {
        # "email": "user@example.com",
        # "hashedPassword": "$2b$12$abc123somehashedpassword",
        # "role": "driver",
        # "fullName": "John Doe",
        # "registrationDate": "2025-03-24T10:00:00Z"
        # }

        # Verify password
        if not verifyPassword(userDataInput.password, userDataDB["hashedPassword"]):
            raise HTTPException(
                status_code=401,
                detail={
                    "status": "fail",
                    "message": "Email atau password salah",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # check email is verified
        if not userDataDB.get("isEmailVerified"):
            raise HTTPException(
                status_code=401,
                detail={
                    "status": "fail",
                    "message": "Email belum diverifikasi, mohon check email anda",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

        # Generate token
        userData={
            "userId": userDataDB["userId"],
            "email": userDataDB["email"],
            "role": userDataDB["role"],
            "username": userDataDB["username"]
            }
        token = createAccessToken(userData)
        userData.update({"token": token}) # Add token to data dictionary

        return {
            "status": "success",
            "message": "Login berhasil",
            "data": userData
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error while logging in user: {str(e)}")  
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan pada server: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

async def requestResetPassword (emailUser) :
    """Request a password reset link"""
    try : 
        # Check if email exists
        userDocs = (
            db.collection("userCollection")   
            .where(filter=FieldFilter("email", "==", emailUser))
            .limit(1)
            .get()
        )
        
        if not len(userDocs) > 0: 
            return {
                "status": "success",
                "message": "Permintaan reset password berhasil dikirim!"
            }
        userData = userDocs[0].to_dict()
        userId = userData.get("userId")
        
        # save otp to userCollection
        otpData = OtpVerificationModel.generate()
        db.collection("userCollection").document(userId).update({
            "otp": otpData.otp,
            "otpTimestamp": otpData.expiresAt
        })

        # Generate current date in WIB format
        current_date_wib = convert_utc_to_wib(datetime.now(timezone.utc))
        formatted_date = current_date_wib.strftime("%A, %d %B %Y, %H:%M WIB")

        html_content = renderTemplate(
            "reset_password_email.html",
            username=userData.get('username', ''),
            otp=otpData.otp,
            current_date=formatted_date
        )

        result = sendEmail (
            to_email = emailUser,
            subject = "Permintaan Reset Password LokaTrack",
            html_content=html_content
        )

        if result ["status"] == "error":
            logger.error(f"Failed to send password reset email: {result['message']}")
            # Continue anyway to avoid revealing if the email exists
        
        return {
            "status": "success",
            "message": "Permintaan reset password berhasil dikirim!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error while requesting password reset: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan pada server: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
async def resetPassword (userDataInput) : 
    """ Reset Password by OTP"""
    try : 
        # Check if email exists
        userDocs = (
            db.collection("userCollection")   
            .where(filter=FieldFilter("email", "==", userDataInput.email))
            .limit(1)
            .get()
        )
        
        if not len(userDocs) > 0: 
            raise HTTPException(
                status_code=401,
                detail={
                    "status": "fail",
                    "message": "Email tidak terdaftar",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        userData = userDocs[0].to_dict()
        userId = userData.get("userId") 
        otp = userData.get("otp")
        otpTimestamp = userData.get("otpTimestamp")

        if not otp or not otpTimestamp:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "OTP tidak ditemukan",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

        if userDataInput.otp != otp:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "OTP tidak valid",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

        # Check if OTP is expired
        if datetime.now(timezone.utc) > otpTimestamp:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "OTP sudah kadaluarsa",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        # Check password length
        if len (userDataInput.newPassword) < 8 :
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "Password harus memiliki minimal 8 karakter",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        # Check if password and password confirmation match
        if userDataInput.newPassword != userDataInput.newPasswordConfirmation: 
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "Password baru dan password konfirmasi tidak sama",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        # Update password
        newPasswordHash = getPasswordHash(userDataInput.newPassword)
        db.collection("userCollection").document(userId).update({
            "hashedPassword": newPasswordHash,
            # Remove OTP and timestamp after successful reset
            "otp": None,
            "otpTimestamp": None,
            "lastUpdate": datetime.now(timezone.utc)
        })

        return {
            "status": "success",
            "message": "Password berhasil direset!"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error while resetting password: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan pada server: {str(e)}",
                "timestamp": datetime.now(timezone.utc)().isoformat(),
            })
    

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
            detail=("Sever Error while sending verification email: {str(e)}")
        )
        
async def verifyEmail(token: str):
    """ Process email verification and return appropriate HTML response """
    try:
        # Find user Data based on Token
        userDoc = (
            db.collection("userCollection")
            .where(filter=FieldFilter("emailVerificationToken", "==", token))
            .limit(1)
            .get()
        )

        if len (userDoc) == 0:
             # trigger error
            raise HTTPException(
                status_code=400,
                detail="User not Found"
            )

        userData = userDoc[0].to_dict()
        emailVerificationTokenExpiry = userData.get("emailVerificationTokenExpiry")
        # Check if token is expired
        if datetime.now(timezone.utc) > emailVerificationTokenExpiry:
            raise HTTPException(
                status_code=400,
                detail="Token expired"
            )
        
        # # Update user data to mark email as verified and delete other data
        # userData.pop("emailVerificationToken")
        # userData.pop("emailVerificationTokenExpiry")
        userData.update({
            "emailVerificationToken": DELETE_FIELD,
            "emailVerificationTokenExpiry": DELETE_FIELD, 
            "countResendVerificationEmail": DELETE_FIELD,
            "isEmailVerified": True,
            "lastUpdate": datetime.now(timezone.utc)
        })
        db.collection("userCollection").document(userData["userId"]).update(userData)
        
        # Render success template
        html_content = renderTemplate(
            "template_email_verification_success.html",
            frontend_url=MOBILE_APP_URL
        )
        
        return HTMLResponse(content=html_content)
    
    except HTTPException as e:
        # Render failure template
        logger.error(f"Email verification failed: {str(e)}")
        html_content = renderTemplate(
            "template_email_verification_failed.html",
            frontend_url=MOBILE_APP_URL
        )
        
        return HTMLResponse(content=html_content, status_code=e.status_code)

    