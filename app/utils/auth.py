from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.security import verifyAccessToken
from datetime import datetime

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency for protected routes that returns the current user data from token"""
    try:
        token = credentials.credentials
        payload = verifyAccessToken(token)
        return payload
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "fail",
                "message": f"Gagal mengautentikasi: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )