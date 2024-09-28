from sqlalchemy import Column, Integer, String
from config.db_connect import Base

class User(Base):
    __tablename__ = "user_accounts"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    firstname = Column(String)
    lastname = Column(String)
    password = Column(String)
    access_role = Column(Integer, default=0)



from pydantic import BaseModel


class RegisterUser(BaseModel):
    email: str
    password: str
    firstname: str
    lastname: str

class LoginUser(BaseModel):
    email:str
    password: str

class ChangePasswordUser(BaseModel):
    current_password: str
    new_password: str

class ChangeInfoUser(BaseModel):
    email: str
    firstname: str
    lastname: str

 
class SendToken(BaseModel):  ## forgot password
    email: str
    
 



class ResetNewPassword(BaseModel):
    token: str
    new_password: str