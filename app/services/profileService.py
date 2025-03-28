from app.config.firestore import db
from app.utils.security import getPasswordHash, verifyPassword
from fastapi import HTTPException
from datetime import datetime

async def getUserProfile(currentUser):
    """Get user profile"""
    userCollection = db.collection("userCollection")
    userDoc = userCollection.document(currentUser["userId"]).get()
    
    if userDoc.exists:
        userData = userDoc.to_dict()
        userData.pop("hashedPassword", None) # Remove hashed password from response
        return {
            "status": "success",
            "data": userData
        }
    else:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "fail",
                "message": "User tidak ditemukan",
                "timestamp": datetime.now().isoformat()
            }
        )
    
async def updateUsernameService(usernameDataInput, currentUser):
    """Update username"""
    userCollection = db.collection("userCollection")
    userDoc = userCollection.document(currentUser["userId"]).get()
    
    if userDoc.exists:
        userCollection.document(currentUser["userId"]).update(usernameDataInput.dict())
        return {
            "status": "success",
            "message": "Username berhasil diubah"
        }
    else:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "fail",
                "message": "Update username gagal",
                "timestamp": datetime.now().isoformat()
            }
        )
    
async def updatePhoneNumberService(phoneDataInput, currentUser):
    """Update Phone Numer"""
    userCollection = db.collection("userCollection")
    userDoc = userCollection.document(currentUser["userId"]).get()
    
    if userDoc.exists:
        userCollection.document(currentUser["userId"]).update(phoneDataInput.dict())
        return {
            "status": "success",
            "message": "Nomor telepon berhasil diubah"
        }
    else:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "fail",
                "message": "Update nomor telepon gagal",
                "timestamp": datetime.now().isoformat()
            }
        )
    
async def updatePasswordService(passwordDataInput, currentUser):
    """Update Password"""
    try : 
        userCollection = db.collection("userCollection")
        userDoc = userCollection.document(currentUser["userId"]).get()  
        userDocs = userDoc.to_dict()

        if not userDoc.exists:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "fail",
                    "message": "User tidak ditemukan",
                    "timestamp": datetime.now().isoformat()
                }
            )

        if not verifyPassword(passwordDataInput.currentPassword, userDocs["hashedPassword"]):
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "Password lama anda salah",
                    "timestamp": datetime.now().isoformat()
                }
            )
    
        if passwordDataInput.currentPassword == passwordDataInput.newPassword:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "Password baru tidak boleh sama dengan password lama",
                    "timestamp": datetime.now().isoformat()
                }
            )

        if passwordDataInput.newPassword != passwordDataInput.newPasswordConfirmation:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "Password baru dan konfirmasi password tidak sama",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # if new password < 8 characters
        if len(passwordDataInput.newPassword) < 8:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "Password baru harus memiliki minimal 8 karakter",
                    "timestamp": datetime.now().isoformat()
                }
            )

        newHashedPassword = getPasswordHash(passwordDataInput.newPassword)
        newData = {
            "hashedPassword": newHashedPassword,
            "lastUpdate": datetime.now().isoformat()
        }
        userCollection.document(currentUser["userId"]).update(newData)
        return {
            "status": "success",
            "message": "Password berhasil diubah"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )
    
