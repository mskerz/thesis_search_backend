from random import random
from typing import Optional
from fastapi import Depends, HTTPException, status,Response
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone

from config.db_connect import SessionLocal
from model.user import User
# Load settings (Assuming settings.py is in the same directory)
from dotenv import load_dotenv
import os
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
SECRET_KEY_RESET = os.getenv('SECRET_KEY_RESET')
JWT_EXPIRATION_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login",scheme_name="JwtBearer")
jwt_scheme = HTTPBearer(auto_error=False)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(plain_password):
    return pwd_context.hash(plain_password)

def create_access_token(user: User):
    """
    Creates a JSON Web Token (JWT) for authentication.

    Args:
        user (User object): The user object containing relevant data.

    Returns:
        str: The encoded JWT token.
    """
    try:
        # Create payload dictionary with user data
        data = {
            "user_id": user.user_id,
            "email": user.email,
            "firstname": user.firstname,
            "lastname": user.lastname,
            "access_role": user.access_role
        }

        # Set expiration time
        expire = datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(minutes=JWT_EXPIRATION_MINUTES)
        data.update({"exp": expire})

        # Encode the token using the secret key and algorithm
        encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm="HS256")
        # save the token in cookie "access_token"

        return encoded_jwt

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

def get_current_user(token: str = Depends(jwt_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token.credentials,SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")

        if user_id is None:
            raise JWTError("Could not find user ID in token")

        # Import User model to avoid circular imports
        # Query user directly from the database using SQLAlchemy
        db = SessionLocal()
        user = db.query(User).filter(User.user_id == user_id).first()
        db.close()
        if not user:
            raise JWTError("User not found in database")

        return user
    except JWTError as e:
        raise credentials_exception from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Unauthorized to access.")


import uuid

 ## reset password
    # encode email token
def encode_email_token(email: str, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = {"sub": email}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY_RESET, algorithm="HS256")
    return encoded_jwt
    # decode email token


def decode_email_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY_RESET, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
        return email
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    

 