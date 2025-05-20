import urllib
from urllib.parse import unquote
from app.config.firestore import db
from fastapi import HTTPException
from datetime import datetime, timezone, timedelta
from app.utils.time import convert_utc_to_wib
from google.cloud.firestore import FieldFilter
import logging
from fastapi import Query
from app.config.sqlite import get_recent_gps_data
from typing import Optional

logger = logging.getLogger(__name__)

async def getAllUsers(currentUser):
    try : 
        # Check if user is admin
        if currentUser["role"] not in ["admin"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "status": "fail",
                    "message": "Anda tidak memiliki akses untuk melihat user!",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Get all users from firestore
        usersDoc = (
            db.collection("userCollection")
            .where(filter=FieldFilter("isEmailVerified", "==", True))
            .stream()
        )
        usersList = []
        adminList = []
        driverList = []
        # usersList = {
        #     "userId": "3e02b584-0b6b-4a3e-b20b-0882999bce71",
        #     "userData": {
        #         "name": "Dummy User",
        #         "email": "dfada@gmail.com"
        #     }
        # }
        for user in usersDoc:
            userData = user.to_dict()
            userData.pop("hashedPassword", None)  # Remove password from user data
            data = {
                "userId:" : userData.get("userId"),
                "userData": userData
            }
            usersList.append(data)

        return {
            "status": "success",
            "message": "Success get data users!",
            "data": usersList,
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
    

async def get_admin_dashboard_service(currentUser):
    """Get admin dashboard statistics"""
    try:
        if currentUser["role"] not in ["admin"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "status": "fail",
                    "message": "Anda tidak memiliki akses untuk melihat user!",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )        
        # Get total user count
        user_count = len(list(db.collection("userCollection").stream()))
        
        # Get user counts by role
        admin_users = len(list(db.collection("userCollection")
                              .where(filter=FieldFilter("role", "==", "admin"))
                              .stream()))
        
        driver_users = len(list(db.collection("userCollection")
                               .where(filter=FieldFilter("role", "==", "driver"))
                               .stream()))
        
        # Get tracker count
        tracker_count = len(list(db.collection("trackerCollection").stream()))
        
        # Get delivery counts by status
        delivery_statuses = ["On Delivery", "Check-in", "Check-out", "Return"]
        delivery_counts = {}
        
        for status in delivery_statuses:
            count = len(list(db.collection("packageDeliveryCollection")
                            .where(filter=FieldFilter("deliveryStatus", "==", status))
                            .stream()))
            delivery_counts[status] = count
        
        # Get total delivery count
        total_deliveries = sum(delivery_counts.values())
        
        # Get recent deliveries
        recent_deliveries = []
        recent_delivery_docs = (
            db.collection("packageDeliveryCollection")
            .order_by("lastUpdateTime", direction="DESCENDING")
            .limit(5)
            .stream()
        )
        
        for doc in recent_delivery_docs:
            delivery_data = doc.to_dict()
            # Convert time fields
            for time_field in ["deliveryStartTime", "checkInTime", "checkOutTime", "returnTime", "lastUpdateTime"]:
                if time_field in delivery_data and delivery_data[time_field]:
                    delivery_data[time_field] = convert_utc_to_wib(delivery_data[time_field]).isoformat()
            
            recent_deliveries.append(delivery_data)
        
        return {
            "status": "success",
            "message": "Admin dashboard data retrieved successfully",
            "data": {
                "userStats": {
                    "totalUsers": user_count,
                    "adminUsers": admin_users,
                    "driverUsers": driver_users
                },
                "trackerStats": {
                    "totalTrackers": tracker_count
                },
                "deliveryStats": {
                    "totalDeliveries": total_deliveries,
                    "statusCounts": delivery_counts
                },
                "recentDeliveries": recent_deliveries
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving admin dashboard: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

async def getAllUsers(role=None, status=None, email_verified=None, search=None, limit=100, offset=0):
    """Get all users with optional filtering"""
    try:
        # Base query
        query = db.collection("userCollection")
        
        # Apply filters
        if role:
            query = query.where(filter=FieldFilter("role", "==", role))
        
        if status:
            query = query.where(filter=FieldFilter("status", "==", status))
        
        if email_verified is not None:
            query = query.where(filter=FieldFilter("isEmailVerified", "==", email_verified))
        
        # Note: For more complex queries like search, we need to get all data and filter in Python
        # since Firestore doesn't support OR conditions across fields
        
        # Get data with pagination
        user_docs = list(query.stream())
        total_count = len(user_docs)
        
        # Apply search filter if provided (this must be done in Python)
        if search:
            search = search.lower()
            filtered_docs = []
            for doc in user_docs:
                user_data = doc.to_dict()
                username = user_data.get("username", "").lower()
                email = user_data.get("email", "").lower()
                
                if search in username or search in email:
                    filtered_docs.append(doc)
            
            user_docs = filtered_docs
            filtered_count = len(user_docs)
        else:
            filtered_count = total_count
        
        # Apply pagination
        paginated_docs = user_docs[offset:offset + limit]
        
        # Format user data
        users = []
        for doc in paginated_docs:
            user_data = doc.to_dict()
            # Remove sensitive fields
            user_data.pop("hashedPassword", None)
            user_data.pop("emailVerificationToken", None)
            user_data.pop("emailVerificationTokenExpiry", None)
            user_data.pop("otp", None)
            user_data.pop("otpTimestamp", None)
            
            # Convert dates to WIB
            if "registrationDate" in user_data and user_data["registrationDate"]:
                user_data["registrationDate"] = convert_utc_to_wib(user_data["registrationDate"]).isoformat()
            
            if "lastUpdate" in user_data and user_data["lastUpdate"]:
                user_data["lastUpdate"] = convert_utc_to_wib(user_data["lastUpdate"]).isoformat()

            data = {
                "userId:" : user_data.get("userId"),
                "userData": user_data
            }
            users.append(data)
        
        return {
            "status": "success",
            "message": "Users retrieved successfully",
            "data": {
                "users": users,
                "pagination": {
                    "total": total_count,
                    "filtered": filtered_count,
                    "offset": offset,
                    "limit": limit
                }
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

async def assign_tracker(currentUser, userId, trackerId):
    """Assign a tracker to a user"""
    try:
        # Check if user is admin
        if currentUser["role"] not in ["admin"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "status": "fail",
                    "message": "Anda tidak memiliki akses!",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

        # Check if user exists
        user_doc = db.collection("userCollection").document(userId).get()
        if not user_doc.exists:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "fail",
                    "message": f"User dengan ID '{userId}' tidak ditemukan",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Check if tracker exists
        tracker_doc = db.collection("trackerCollection").document(trackerId).get()
        if not tracker_doc.exists:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "fail",
                    "message": f"Tracker dengan ID '{trackerId}' tidak ditemukan",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Check if tracker is already assigned to another user
        users_with_tracker = list(db.collection("userCollection")
                                 .where(filter=FieldFilter("trackerId", "==", trackerId))
                                 .stream())
        
        for doc in users_with_tracker:
            if doc.id != userId:
                user_data = doc.to_dict()
                raise HTTPException(
                    status_code=409,
                    detail={
                        "status": "fail",
                        "message": f"Tracker sudah digunakan oleh user '{user_data.get('username')}' (ID: {doc.id})",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
        
        # Update user with tracker ID
        user_data = user_doc.to_dict()
        db.collection("userCollection").document(userId).update({
            "trackerId": trackerId,
            "lastUpdate": datetime.now(timezone.utc)
        })
        
        return {
            "status": "success",
            "message": f"Tracker berhasil ditetapkan kepada user '{user_data.get('username')}'",
            "data": {
                "userId": userId,
                "username": user_data.get("username"),
                "trackerId": trackerId,
                "assignedAt": convert_utc_to_wib(datetime.now(timezone.utc)).isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning tracker: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

async def get_all_delivery_packages_service(status=None, driver_id=None, date_from=None, date_to=None, limit=100, offset=0):
    """Get all delivery packages with optional filtering"""
    try:
        # Base query
        query = db.collection("packageDeliveryCollection")
        
        # Apply filters
        if status:
            query = query.where(filter=FieldFilter("deliveryStatus", "==", status))
        
        if driver_id:
            query = query.where(filter=FieldFilter("driverId", "==", driver_id))
        
        # Note: For date filtering, we need to get data and filter in Python
        # since complex date operations aren't fully supported in Firestore queries
        
        # Get data
        delivery_docs = list(query.stream())
        total_count = len(delivery_docs)
        
        # Apply date filters if provided
        if date_from or date_to:
            filtered_docs = []
            
            for doc in delivery_docs:
                delivery_data = doc.to_dict()
                delivery_time = delivery_data.get("deliveryStartTime")
                
                if not delivery_time:
                    continue
                
                # Convert string date filters to datetime
                try:
                    if date_from:
                        from_date = datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                        if delivery_time < from_date:
                            continue
                    
                    if date_to:
                        # Add a day to include the entire end day
                        to_date = datetime.strptime(date_to, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)
                        if delivery_time >= to_date:
                            continue
                    
                    filtered_docs.append(doc)
                except ValueError:
                    # Skip invalid date formats
                    continue
            
            delivery_docs = filtered_docs
        
        filtered_count = len(delivery_docs)
        
        # Apply pagination
        paginated_docs = delivery_docs[offset:offset + limit]
        
        # Format delivery data
        deliveries = []
        for doc in paginated_docs:
            delivery_data = doc.to_dict()
            
            # Convert time fields to WIB
            for time_field in ["deliveryStartTime", "checkInTime", "checkOutTime", "returnTime", "lastUpdateTime"]:
                if time_field in delivery_data and delivery_data[time_field]:
                    delivery_data[time_field] = convert_utc_to_wib(delivery_data[time_field]).isoformat()
            
            deliveries.append(delivery_data)
        
        return {
            "status": "success",
            "message": "Delivery packages retrieved successfully",
            "data": {
                "deliveries": deliveries,
                "pagination": {
                    "total": total_count,
                    "filtered": filtered_count,
                    "offset": offset,
                    "limit": limit
                }
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving delivery packages: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

async def getGPSData(trackerId, limit, currentUser):
    """Get recent GPS data from SQLite database"""
    try:
        # Check if user is admin
        if currentUser["role"] not in ["admin"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "status": "fail",
                    "message": "Anda tidak memiliki akses untuk melihat user!",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        data = get_recent_gps_data(trackerId=trackerId, limit=limit)
        return {
            "status": "success",
            "message": "GPS data retrieved successfully",
            "data": {
                "gps_data": data,
                "count": len(data)
            }
        }
    except Exception as e:
        logger.error(f"Error while retrieving GPS data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )