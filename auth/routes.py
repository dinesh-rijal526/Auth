from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from .schemas import CreateUserModel, UserModel, EmailModel
from .services import UserServices
from db.main import get_session

auth_router = APIRouter()
user_services = UserServices()

@auth_router.post('/register', response_model=UserModel)
async def register_user(user_data:CreateUserModel, session:AsyncSession = Depends(get_session)):
    user = await user_services.create_user(user_data, session)
    return user

@auth_router.post('/user')
async def user_exist(data:EmailModel, session:AsyncSession = Depends(get_session)):
    email = data.email
    user = await user_services.get_user_by_email(email, session)
    if user:
        return {'message':'User exists'}
    else:
        return {'message':'User doesnot exist'}
    