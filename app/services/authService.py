from app.config.firestore import db
from app.models.userModel import UserModel
from app.utils.security import getPasswordHash, verifyPassword, createAccessToken
from fastapi import HTTPException
from datetime import datetime
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
                    "message": "Password dan password password tidak sama",
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