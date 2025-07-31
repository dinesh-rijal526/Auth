from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from .models import User
from .schemas import CreateUserModel
from .utils import generate_hash_password

class UserServices():
    async def get_user_by_email(self, email:str, session:AsyncSession):
        statement = select(User).where(User.email == email)
        result = await session.exec(statement)
        user = result.first()
        return user
    
    async def email_exist(self, email:str, session:AsyncSession):
        statement = select(User).where(User.email == email)
        user = await session.exec(statement)
        if user.first() is None:
            return False
        else:
            return True
        
    async def username_exist(self, username:str, session:AsyncSession):
        statement = select(User).where(User.username == username)
        user_name = await session.exec(statement)
        if user_name.first() is None :
            return False
        else:
            return True
    
    async def create_user(self, user_data:CreateUserModel, session:AsyncSession):
        user_data_dict = user_data.model_dump()
        new_user = User(
            **user_data_dict
        ) 
        
        new_user.hash_password = generate_hash_password(user_data_dict['password'])
        session.add(new_user)
        await session.commit()
        return new_user
        
    async def update_user(self, user:User , user_data: dict,session:AsyncSession):

        for k, v in user_data.items():
            setattr(user, k, v)

        await session.commit()

        return user 