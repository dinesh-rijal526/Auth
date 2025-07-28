from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import timedelta, datetime
import uuid
from .schemas import CreateUserModel, UserModel, LoginUserModel
from .services import UserServices
from db.main import get_session
from .utils import create_access_token, decode_token, verify_password
from .dependencies import RefreshTokenBearer, AccessTokenBearer
from db.redis import add_jti_to_blocklist

auth_router = APIRouter()
user_services = UserServices()

REFRESH_TOKEN_EXPIRY = 2

@auth_router.post('/signup', response_model=UserModel, status_code=status.HTTP_201_CREATED)
async def register_user(user_data:CreateUserModel, session:AsyncSession = Depends(get_session)):
    email = user_data.email
    username = user_data.username
    user_exist = await user_services.email_exist(email, session)
    username_exist = await user_services.username_exist(username, session)
    if user_exist:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='User with this email already exist')
    
    if username_exist:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='User with this username already exist')
    
    new_user = await user_services.create_user(user_data, session)
    return new_user

@auth_router.post('/login')
async def login_user(login_data:LoginUserModel, session:AsyncSession = Depends(get_session)):
    email = login_data.email
    password = login_data.password
    
    user = await user_services.get_user_by_email(email, session) 
    
    if user is not None :
        password_valid = verify_password(password, user.hash_password)
        
        if password_valid:
            access_token = create_access_token(
                user_data={
                    'email' : user.email,
                    'user_uid' : str(uuid.uuid4)
                }
            )
            
            refresh_token = create_access_token(
                user_data={
                    'email' : user.email,
                    'user_uid' : str(uuid.uuid4)
                },
                refresh=True,
                expiry=timedelta(days=REFRESH_TOKEN_EXPIRY)
            )
            
            return JSONResponse(
                content={
                    'message' : 'Login Successfully',
                    'access_token' : access_token,
                    'refresh_token' : refresh_token,
                    'user' : {
                        'uid' : str(user.uid),
                        'name' : user.first_name,
                        'email' : user.email
                    }
                }
            )
            
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid Email Or Password')

@auth_router.get("/refresh_token")
async def get_new_access_token(token_details: dict = Depends(RefreshTokenBearer())):
    expiry_timestamp = token_details["exp"]

    if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
        new_access_token = create_access_token(user_data=token_details["user"])

        return JSONResponse(content={"access_token": new_access_token})

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Or expired token"
    )
     
   
@auth_router.post('/logout')
async def revook_token(token_details:dict = Depends(AccessTokenBearer())):
    jti = token_details['jti']
    await add_jti_to_blocklist(jti)
    return JSONResponse(
        content={
            'message':'Loggout Successfully'
        },
        status_code=status.HTTP_200_OK
    )
    