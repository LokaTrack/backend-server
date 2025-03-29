from app.config.firestore import db
from app.models.userModel import UserModel
from app.utils.security import getPasswordHash, verifyPassword, createAccessToken
from fastapi import HTTPException
from datetime import datetime
from firebase_admin import auth
import uuid
from datetime import datetime, timedelta, timezone


async def getDashboard (currentUser):
    """Get user dashboard data"""
    try: 
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1) - timedelta(seconds=1)
        # statistic 
        statistics = {
            "dikirim": 0,
            "sampai": 0,
            "selesai": 0,
            "dikembalikan": 0,
            "others": 0,
            "percentage" : 0
        }

        deliveryDocs = (
            db.collection("packageDeliveryCollection")
            .where("driverId", "==", currentUser["userId"])
            .where("deliveryStartTime", ">=", today_start)
            # .where("deliveryStartTime", "<=", today_end)
            .get()
        )

        if not deliveryDocs:
            return {
                "status": "success",
                "message": f"Tidak ada data pengiriman hari ini untuk user '{currentUser['username']}'.",
                "data": {
                    "statistics": statistics,
                    "recentOrder": []
                },
                "timestamp": datetime.now().isoformat()
            }    
        recentOrder = [deliveryDoc.to_dict() for deliveryDoc in deliveryDocs]
        totalPackage = len(recentOrder)
        statistics["totalPackage"] = totalPackage

        # for x in recentOrder :
        #     if x.get("deliveryStatus") == "dikirim":
        #         statistics["dikirim"] += 1
        #     elif x.get("deliveryStatus") == "sampai":
        #         statistics["sampai"] += 1
        #     elif x.get("deliveryStatus") == "diterima":
        #         statistics["diterima"] += 1
        #     elif x.get("deliveryStatus") == "dikembalikan":
        #         statistics["dikembalikan"] += 1
        #     else :
        #         statistics["others"] += 1

        status_mapping = {"dikirim": "dikirim", "sampai": "sampai", "selesai": "selesai", "dikembalikan": "dikembalikan"}

        for x in recentOrder:
            key = status_mapping.get(x.get("deliveryStatus"), "others")
            statistics[key] += 1

        if totalPackage > 0:
            # Consider both selesai and dikembalikan as completed
            completed = statistics["selesai"] + statistics["dikembalikan"]
            statistics["percentage"] = int((completed / totalPackage) * 100)

        data = {
                "statistics" : statistics,
                "recentOrder": recentOrder,
        }
        return {
            "status": "success",
            "message": "Mengambil data dashboard berhasil",
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e   :
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

