from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from config.db_connect import Base

class Advisor(Base):
    __tablename__ = "advisor"

    advisor_id = Column(Integer, primary_key=True, index=True)
    advisor_name = Column(String)

class Advisors(BaseModel):
    advisor_id: int
    advisor_name: str

class AdvisorForm(BaseModel):
    advisor_name: str
