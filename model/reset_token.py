from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from config.db_connect import Base


class ResetPasswordTokens(Base):
    __tablename__ = "reset_password_tokens"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user_accounts.user_id'))  # Foreign key relationship with user_accounts table
    user = relationship("User", foreign_keys=[user_id]) # Define relationship with User model
    token = Column(String)
    expired_status = Column(Integer,default=0)
    expire_date = Column(DateTime)
    def __init__(self, user_id: int, token: str):
        self.user_id = user_id
        self.token = token
        self.expire_date = datetime.now() + timedelta(seconds=600)


