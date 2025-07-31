from sqlmodel import SQLModel, Column, Field
import sqlalchemy.dialects.postgresql as pg
from datetime import datetime
import uuid

class User(SQLModel, table=True):
    uid : uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), nullable=False, primary_key=True, default=uuid.uuid4))
    first_name : str 
    middle_name : str | None = None
    last_name : str
    username : str = Field(unique=True, nullable=False)
    email : str = Field(unique=True, nullable=False)
    hash_password : str = Field(exclude=True, nullable=False)
    is_verified : bool = Field(default=False)
    role : str = Field(sa_column=Column(pg.VARCHAR, nullable=False, server_default="user"))
    created_at : datetime = Field(sa_column=Column(pg.TIMESTAMP, nullable=False, default=datetime.now))
    updated_at : datetime = Field(sa_column=Column(pg.TIMESTAMP, nullable=False, default=datetime.now, onupdate=datetime.now))
    
    def __repr__(self):
        return f"<User {self.username}>"
    