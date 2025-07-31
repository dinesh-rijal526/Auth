from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import timedelta, datetime
import uuid
from .schemas import CreateUserModel, UserModel, LoginUserModel, EmailModel
from .services import UserServices
from db.main import get_session
from .utils import create_access_token, decode_token, verify_password, create_url_safe_token, decode_url_safe_token
from .dependencies import RefreshTokenBearer, AccessTokenBearer, RoleChecker, get_current_user
from db.redis import add_jti_to_blocklist
from mail import mail, create_message
from config import Config

auth_router = APIRouter()
user_services = UserServices()
role_checker = RoleChecker(["admin","user"])

REFRESH_TOKEN_EXPIRY = 2

@auth_router.post('/send-mail')
async def send_mail(emails:EmailModel):
    email_address = emails.addresses
    html = '<h1>Welcom to the app.</h1>'
    message = create_message(
        recipients=email_address,
        subject='Welcome',
        body=html
    )
    await mail.send_message(message)
    return {'message': 'Email sent successfully'}
    

@auth_router.post('/signup', status_code=status.HTTP_201_CREATED)
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

    token = create_url_safe_token({"email": email})

    link = f"http://{Config.DOMAIN}/auth/verify/{token}"

    html_message = f"""
    <h1>Verify your Email</h1>
    <p>Please click this <a href="{link}">link</a> to verify your email</p>
    """

    message = create_message(
        recipients=[email], subject="Verify your email", body=html_message
    )

    await mail.send_message(message)

    return {
        "message": "Account Created! Check email to verify your account",
        "user": new_user,
    }
    
@auth_router.get("/verify/{token}")
async def verify_user_account(token: str, session: AsyncSession = Depends(get_session)):

    token_data = decode_url_safe_token(token)

    user_email = token_data.get("email")

    if user_email:
        user = await user_services.get_user_by_email(user_email, session)

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'meeeage':'User not found'})

        await user_services.update_user(user, {"is_verified": True}, session)

        return JSONResponse(
            content={"message": "Account verified successfully"},
            status_code=status.HTTP_200_OK,
        )

    return JSONResponse(
        content={"message": "Error occured during verification"},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

@auth_router.post('/login')
async def login_user(login_data:LoginUserModel, session:AsyncSession = Depends(get_session)):
    email = login_data.email
    password = login_data.password
    
    user = await user_services.get_user_by_email(email, session) 
    user_is_verified = user.is_verified
    if user is not None :
        if user_is_verified :
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
        
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Your account is not Verified. Please Verify')    
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid Email Or Password')

@auth_router.get("/refresh_token")
async def get_new_access_token(token_details: dict = Depends(RefreshTokenBearer()), _ : bool = Depends(role_checker)):
    expiry_timestamp = token_details["exp"]

    if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
        new_access_token = create_access_token(user_data=token_details["user"])

        return JSONResponse(content={"access_token": new_access_token})

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Or expired token"
    )

@auth_router.get('/me',)
async def get_current_user(user = Depends(get_current_user), _ : bool = Depends(role_checker)):
    return user   
   
@auth_router.post('/logout')
async def revook_token(token_details:dict = Depends(AccessTokenBearer()), _ : bool = Depends(role_checker)):
    jti = token_details['jti']
    await add_jti_to_blocklist(jti)
    return JSONResponse(
        content={
            'message':'Loggout Successfully'
        },
        status_code=status.HTTP_200_OK
    )
    

    