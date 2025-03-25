from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from app.models.userModel import UserCreateModel, UserLoginModel
from app.services.authService import registerUser, loginUser #, registerUserWithFirebase

router = APIRouter(prefix="/api/v1", tags=["Authentication"])

@router.post("/register", status_code=201)
async def register(userDataInput: UserCreateModel):
    """Register a new user"""
    try:
        result = await registerUser(userDataInput)
        # return JSONResponse(
        #     status_code=201,
        #     content=result
        # )
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )
    
# @router.post("/register-with-firebase", status_code=201)
# async def register(userDataInput: UserCreateModel):
#     """Register a new user"""
#     try:
#         result = await registerUserWithFirebase(userDataInput)
#         # return JSONResponse(
#         #     status_code=201,
#         #     content=result
#         # )
#         return result
#     except HTTPException as e:
#         return JSONResponse(
#             status_code=e.status_code,
#             content=e.detail
#         )

@router.post("/login")
async def login(userDataLogin: UserLoginModel):
    """Login an existing user and return a token"""
    try:
        print("try to login")
        result = await loginUser(userDataLogin)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )
    

    """Retrieve all users from the database"""
    try:
        result = await getAllUsers()
        return JSONResponse(
            status_code=200,
            content=result
        )
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )