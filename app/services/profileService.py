from app.config.firestore import db
from app.models.authModel import EmailVerificationModel
from app.utils.security import getPasswordHash, verifyPassword
from app.utils.storeImage import uploadImageToStorage, uploadBytesToStorage
from app.utils.emailVerification import sendVerificationEmail
from app.utils.compress import compress_image
from fastapi import HTTPException
from datetime import datetime, timezone
from google.cloud.firestore import FieldFilter, DELETE_FIELD
import logging
logger = logging.getLogger(__name__)

async def getUserProfile(currentUser):
    """Get user profile"""
    try : 
        userCollection = db.collection("userCollection")
        userDoc = userCollection.document(currentUser["userId"]).get()

        if not userDoc.exists:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "fail",
                    "message": "User tidak ditemukan",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        userData = userDoc.to_dict()
        userData.pop("hashedPassword", None) # Remove hashed password from response

        # get user delivery statistic
        historyDeliveryDoc = (
            db.collection("packageDeliveryCollection")
            .where(filter=FieldFilter("driverId", "==", currentUser["userId"]))
            .where(filter=FieldFilter("deliveryStatus", "in", ["Check-out", "Return"]))
            .get()
        )

        # statistic 
        deliveredPackages = 0
        returnedPackages = 0
        percentage = 0
        totalDeliveries = 0

        for delivery in historyDeliveryDoc:
            deliveryData = delivery.to_dict()
            totalDeliveries += 1
            if deliveryData["deliveryStatus"] == "Check-out":
                deliveredPackages += 1
            elif deliveryData["deliveryStatus"] == "Return":
                returnedPackages += 1
        totalDeliveries =  deliveredPackages + returnedPackages
        percentage = (deliveredPackages / totalDeliveries) * 100 if totalDeliveries > 0 else 0

        userData.update({
            "deliveredPackages" : deliveredPackages,
            "totalDeliveries" : totalDeliveries,
            "percentage" : percentage
        })    
        return {
            "status": "success",
            "message": "Berhasil mendapatkan profile",
            "data": userData
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
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
                "timestamp": datetime.now(timezone.utc).isoformat()
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
                "timestamp": datetime.now(timezone.utc).isoformat()
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
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

        if not verifyPassword(passwordDataInput.currentPassword, userDocs["hashedPassword"]):
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "Password lama anda salah",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
    
        if passwordDataInput.currentPassword == passwordDataInput.newPassword:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "Password baru tidak boleh sama dengan password lama",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

        if passwordDataInput.newPassword != passwordDataInput.newPasswordConfirmation:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "Password baru dan konfirmasi password tidak sama",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # if new password < 8 characters
        if len(passwordDataInput.newPassword) < 8:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "Password baru harus memiliki minimal 8 karakter",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

        newHashedPassword = getPasswordHash(passwordDataInput.newPassword)
        newData = {
            "hashedPassword": newHashedPassword,
            "lastUpdate": datetime.now(timezone.utc).isoformat()
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
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
async def updateProfilePictureService (profilePictureFile, currentUser): 
    """ Update Profile Picture"""
    try:
        userImage = await profilePictureFile.read()
        file_size = len(userImage)
        max_size = 1024 * 1024 * 10 # 10mb

        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "Ukuran file terlalu besar, maksimal 10MB",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

        # Reset file position 
        await profilePictureFile.seek(0)

        content_type = profilePictureFile.content_type
        if not content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "File harus berupa gambar (jpg, png, gif)",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )    
                        #{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}    
        # filename = f"{currentUser['userId']}_{currentUser['username']}_profile_picture"
        filename = f"{currentUser['userId']}_profile_picture"
        file_extension = profilePictureFile.filename.split(".")[-1]
        full_filename = f"{filename}.{file_extension}"
        
        # Upload file to storage
        # profile_picture_url = await uploadImageToStorage(
        #     profilePictureFile, 
        #     "profile-pictures",  # Folder in storage bucket
        #     full_filename
        # )

        # compressed image
        compressed_image, output_mime = await compress_image(
            image_file=profilePictureFile,
            quality=75,  # Adjust the compression level as needed
            return_buffer=True,
            max_size_kb=1024
        )

        # Upload compressed image to storage 
        profile_picture_url = await uploadBytesToStorage(
            bytes=compressed_image,
            location="profile-pictures", # folder in storage bucket
            fileName=full_filename,
            content_type=output_mime
        )
        
        # Get user data 
        userDoc = (
            db.collection("userCollection")
            .document(currentUser["userId"])
        )
        
        if not userDoc.get().exists:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "fail",
                    "message": "User tidak ditemukan",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Update profile picture URL in database
        userDoc.update({
            "profilePictureUrl": profile_picture_url,
            "lastUpdate": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "status": "success",
            "message": "Foto profil berhasil diperbarui",
            "data": {
                "profilePictureUrl": profile_picture_url
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
async def updateEmailService(userDataInput, currentUser):
    """Update Email"""
    try :
        userRef = (
            db.collection("userCollection")
            .document(currentUser.get("userId"))
            .get()
        )
        if not userRef.exists:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "fail",
                    "message": "User tidak ditemukan",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        userData = userRef.to_dict()
        if userData["email"] == userDataInput.email:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "Email baru tidak boleh sama dengan email lama",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        # Check if email already exists
        docUsers = (
            db.collection("userCollection")   
            .where(filter=FieldFilter("email", "==", userDataInput.email))
            .limit(1)
            .get()
        )
        
        if len(docUsers) > 0:
            existingUserData = docUsers[0].to_dict()
            # Check if email is already verified
            if existingUserData.get("isEmailVerified"):
                raise HTTPException(
                    status_code=400,
                    detail={
                        "status": "fail",
                        "message": "Email baru sudah terdaftar",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
        
        verificationData = EmailVerificationModel.generate()
        # send email 
        await sendVerificationEmail(
            email=userDataInput.email,
            username=currentUser.get("username"),
            emailVerificationToken = verificationData.emailVerificationToken
        )
     
        db.collection("userCollection").document(currentUser.get("userId")).update({
            "email": userDataInput.email,
            "isEmailVerified": False,
            "emailVerificationToken": verificationData.emailVerificationToken,
            "emailVerificationTokenExpiry": verificationData.emailVerificationTokenExpiry,
            "lastUpdate": datetime.now(timezone.utc),
            "countResendVerificationEmail": userData.get("countResendVerificationEmail", 0) + 1
        })

        return {
            "status": "success",
            "message": "Email verifikasi telah dikirim! Silahkan cek email anda untuk memperbaharui email",
            "data": {
                "newEmail": userDataInput.email
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": "Terjadi kesalahan pada server",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
async def updateTrackerService(userDataInput, currentUser): 
    """Update Tracker ID in User Data"""
    try:
        userCollection = db.collection("userCollection")
        userDoc = userCollection.document(currentUser["userId"]).get()
        
        if not userDoc.exists:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "fail",
                    "message": "User tidak ditemukan",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Update tracker ID in user data
        userCollection.document(currentUser["userId"]).update(userDataInput.dict())
        
        return {
            "status": "success",
            "message": "Tracker ID berhasil diperbarui",
            "data": {
                "username": currentUser["username"],
                "trackerId": userDataInput.trackerId
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tracker ID: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )