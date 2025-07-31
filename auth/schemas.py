from pydantic import BaseModel, Field
from typing import List
import uuid

class CreateUserModel(BaseModel):
    first_name : str = Field(max_length=20)
    middle_name : str | None = None
    last_name : str = Field(max_length=20)
    username : str = Field(max_length=20)
    email : str = Field(max_length=50)
    password : str = Field(min_length=8)
    
class UserModel(BaseModel):
    uid : uuid.UUID
    first_name : str 
    middle_name : str | None 
    last_name : str 
    username : str
    email : str
    hash_password : str = Field(exclude=True)
    
class LoginUserModel(BaseModel):
    email : str 
    password : str
    
class EmailModel(BaseModel):
    addresses : List[str]