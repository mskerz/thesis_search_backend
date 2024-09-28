from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid
from jose import JWTError, jwt
from dotenv import load_dotenv
import os

from fastapi import HTTPException
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
SECRET_KEY_RESET = os.getenv('SECRET_KEY_RESET')

def encode_email_token(email: str, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = {"sub": email}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=10)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY_RESET, algorithm="HS256")
    return encoded_jwt
    # decode email token


def decode_email_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY_RESET, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=400, detail="Invalid token")
        return email
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid token")
    

