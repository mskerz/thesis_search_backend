from typing import Optional, Text
from fastapi import Form, UploadFile
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String,Text
from sqlalchemy.orm import relationship
from datetime import timezone,datetime
from config.db_connect import Base

class ThesisDocument(Base):
    __tablename__ ="thesis_document"

    doc_id = Column(Integer, primary_key=True, index=True)
    title_th = Column(String)
    title_en = Column(String)
    user_id = Column(Integer, ForeignKey('user_accounts.user_id'))  # Foreign key relationship with user_accounts table
    user = relationship("User", foreign_keys=[user_id]) 
    advisor_id = Column(Integer, ForeignKey('advisor.advisor_id'))  # Foreign key relationship with advisor table
    advisor = relationship("Advisor", foreign_keys=[advisor_id]) 
    year = Column(Integer)
    abstract = Column(Text)
    recheck_status =Column(Integer,default=0)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True,default=datetime.now())



class ThesisFile(Base):
    __tablename__ ="file_documents"
    file_id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(Integer, ForeignKey('thesis_document.doc_id'))  # Foreign key relationship with user_accounts table
    doc = relationship("ThesisDocument", foreign_keys=[doc_id]) 
    file_name = Column(String)
    file_path = Column(String)

class Term(Base):
    __tablename__ ="term"

    term_id = Column(Integer, primary_key=True, index=True)
    term  = Column(String)
    frequency = Column(Integer)
    doc_id = Column(Integer, ForeignKey('thesis_document.doc_id'))  # Foreign key relationship with user_accounts table
    doc = relationship("ThesisDocument", foreign_keys=[doc_id]) 





class ThesisFormRequest(BaseModel):
    title_th:str
    title_en:str
    advisor_id:int
    year:int



class ThesisDocumentFormat(BaseModel):
    doc_id:int
    title_th:str
    title_en:str
    author_name:str
    advisor_name:str
    year:int
    abstract:str



class ThesisResponse(BaseModel):
    doc_id:int
    title_th: str
    title_en: str
    advisor_id: int
    year: int

class ThesisCheckResponse(BaseModel):
    has_thesis: bool
    thesis: Optional[ThesisResponse] = None
