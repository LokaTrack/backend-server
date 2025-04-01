from app.config.firestore import db
from app.models.userModel import UserModel
from app.models.authModel import OtpVerificationModel
from app.utils.security import getPasswordHash, verifyPassword, createAccessToken
from app.utils.email import sendEmail
from app.utils.template import renderTemplate
from fastapi import HTTPException
from datetime import datetime, timezone
import logging
logger = logging.getLogger(__name__)

async def registerUser(userDataInput):
    """Register a new user"""
    try : 
        # Check if email already exists
        docUsers = (
            db.collection("userCollection")   
            .where("email", "==", userDataInput.email)
            .limit(1)
            .get()
        )

        if len(docUsers) > 0:
            raise HTTPException(
                status_code=409,  
                detail={
                    "status": "fail",
                    "message": "Email ini sudah digunakan",
                    "timestamp": datetime.now().isoformat()
                }
            )
        # Check password length
        if len (userDataInput.password) < 8 :
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "Password harus memiliki minimal 8 karakter",
                    "timestamp": datetime.now().isoformat()
                }
            )
        # Check if password and password confirmation match
        if userDataInput.password != userDataInput.passwordConfirmation: 
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "Password dan password konfirmasi tidak sama",
                    "timestamp": datetime.now().isoformat()
                }
            )

        # Create new user
        # userId = str(uuid.uuid4()) # Generate a random UUID
        newUserData = UserModel(
            # userId=userId,
            email=userDataInput.email,
            username=userDataInput.username,
            hashedPassword=getPasswordHash(userDataInput.password),
            # registrationDate=datetime.now(),
            # fullName=userDataInput.fullName if hasattr(userDataInput, "fullName") else None
        )

        # Save user to Firestore
        newUserDataInDict = newUserData.dict()
        db.collection("userCollection").document(newUserData.userId).set(newUserDataInDict)

        # try:
        #     await send_verification_email(
        #         email=userDataInput.email, 
        #         username=userDataInput.username
        #     )
        # except Exception as email_error:
        #     logger.error(f"Error sending verification email: {str(email_error)}")

        return {
            "status": "success",
            "message": "Akun anda berhasil dibuat!"
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
                "timestamp": datetime.now().isoformat()
            }
        )

async def loginUser(userDataInput):
    """Authenticate a user and return a token"""
    try : 
        # Find user by email
        userDocs = (
        db.collection("userCollection")
        .where("email", "==", userDataInput.email)
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
                    "timestamp": datetime.now().isoformat()
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
                    "timestamp": datetime.now().isoformat()
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
                "timestamp": datetime.now().isoformat()
            }
        )
    

async def requestResetPassword (emailUser) :
    """Request a password reset link"""
    try : 
        # Check if email exists
        userDocs = (
            db.collection("userCollection")   
            .where("email", "==", emailUser)
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

        html_content = renderTemplate(
            "password_reset.html",
            username=userData.get('username', ''),
            otp=otpData.otp
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
                "timestamp": datetime.now().isoformat()
            }
        )
    

async def resetPassword (userDataInput) : 
    """ Reset Password by OTP"""
    try : 
        # Check if email exists
        userDocs = (
            db.collection("userCollection")   
            .where("email", "==", userDataInput.email)
            .limit(1)
            .get()
        )
        
        if not len(userDocs) > 0: 
            raise HTTPException(
                status_code=401,
                detail={
                    "status": "fail",
                    "message": "Email tidak terdaftar",
                    "timestamp": datetime.now().isoformat()
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
                    "timestamp": datetime.now().isoformat()
                }
            )

        if userDataInput.otp != otp:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "OTP tidak valid",
                    "timestamp": datetime.now().isoformat()
                }
            )

        # Check if OTP is expired
        if datetime.now(timezone.utc) > otpTimestamp:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "OTP sudah kadaluarsa",
                    "timestamp": datetime.now().isoformat()
                }
            )
        # Check password length
        if len (userDataInput.newPassword) < 8 :
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "Password harus memiliki minimal 8 karakter",
                    "timestamp": datetime.now().isoformat()
                }
            )
        # Check if password and password confirmation match
        if userDataInput.newPassword != userDataInput.newPasswordConfirmation: 
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "Password baru dan password konfirmasi tidak sama",
                    "timestamp": datetime.now().isoformat()
                }
            )
        # Update password
        newPasswordHash = getPasswordHash(userDataInput.newPassword)
        db.collection("userCollection").document(userId).update({
            "hashedPassword": newPasswordHash,
            # Remove OTP and timestamp after successful reset
            "otp": None,
            "otpTimestamp": None,
            "lastUpdate": datetime.now()
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
                "timestamp": datetime.now().isoformat(),
            })