from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String
from database import Base

class User(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
