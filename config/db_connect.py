from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker,Session
from urllib.parse import quote

# MySQL connection settings
# SQLALCHEMY_DATABASE_URL = "mysql://root:1234@db:3306/thesis_base"

SQLALCHEMY_DATABASE_URL = "mysql://admin:Admin1234@34.142.236.17:3306/thesis_base"
 
#  Create SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)  

# Create a SessionLocal class to handle database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for declarative models
Base = declarative_base()
session =Session
# Dependency to get the database session
def get_db()  : 
    #
    """
    Provides a database session to the dependency injection system.

    Returns:
        Session: An instance of SQLAlchemy session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()