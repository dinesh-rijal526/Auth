from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from .models import User
from .schemas import CreateUserModel
from .utils import generate_hash_password

class UserServices():
    async def get_user_by_email(self, email:str, session:AsyncSession):
        statement = select(User).where(User.email == email)
        result = await session.exec(statement)
        user_email = result.first()
        return user_email
    
    async def user_exist(self, email:str, session:AsyncSession):
        statement = select(User).where(User.email == email)
        user = await session.exec(statement)
        if user is None:
            return False
        else:
            return True
    
    async def create_user(self, user_data:CreateUserModel, session:AsyncSession):
        user_data_dict = user_data.model_dump()
        new_user = User(
            **user_data_dict
        ) 
        
        new_user.hash_password = user_data_dict['password']
        session.add(new_user)
        await session.commit()
        return new_user
        