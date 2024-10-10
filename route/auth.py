from datetime import datetime, timedelta, timezone
from random import choice
from fastapi import APIRouter, Depends, HTTPException, Response,status
from middleware.authentication import verify_password, create_access_token,hash_password,get_current_user,encode_email_token,decode_email_token,JWT_EXPIRATION_MINUTES
from middleware.gmail import sendEmail
from model.reset_token import ResetPasswordTokens as ResetToken
from model.user import ChangeInfoUser, ChangePasswordUser, RegisterUser,LoginUser, User
from pydantic import ValidationError
from config.db_connect import get_db,session,SessionLocal
from model.user import SendToken, ResetNewPassword

router = APIRouter()

# Function to generate a random token
# Function to generate a random token
"""
    [
    "jakkrapan@gmail.com",
    "thongchai@gmail.com",
    "thidarat@gmail.com",
    "patma@gmail.com",
    "patcharin@gmail.com",
    "puttipong@gmail.com",
    "ladawan@gmail.com",
    "waiwut@gmail.com",
    "wissarut@gmail.com",
    "sittidet@gmail.com"
    password : password12345
]

"""
@router.post("/login",tags=["User Account Management"])
async def login(userLogin:LoginUser,response: Response):
    """
    Logs a user in and generates an access token if credentials are valid.

    Args:
        email (str): The user's email address.
        password (str): The user's plain text password.

    Returns:
        dict: A dictionary containing the access token and token type.

    Raises:
        HTTPException: If login fails due to invalid credentials or other errors.
    """
    db = SessionLocal()
    user = db.query(User).filter(User.email == userLogin.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(userLogin.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Generate and return access token
    access_token = create_access_token(user)
    expire = datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(minutes=JWT_EXPIRATION_MINUTES)

    response.set_cookie("access_token", access_token, expires=expire, secure=True, httponly=True)

    return {"status_code": status.HTTP_200_OK,"access_token": access_token}


@router.post("/register",tags=["User Account Management"],)
async def register(user_data: RegisterUser,db:session = Depends(get_db)):
    """
    Registers a new user in the database.

    Args:
        user_data (UserRegistrationRequest): The user registration data.

    Returns:
        dict: A dictionary containing a success message.

    Raises:
        HTTPException: If user registration fails due to duplicate email or other errors.
    """
    try:
        hashed_password = hash_password(plain_password=user_data.password)
        user = User(email=user_data.email, password=hashed_password, firstname=user_data.firstname, lastname=user_data.lastname)
        db.add(user)
        db.commit()
        # Save user to the database or perform other registration logic

        return {"message": "User registration successful","status_code":200}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/user/verify",tags=["User Account Management"])
async def verify_user(current_user: User = Depends(get_current_user)):
    """
    Endpoint to verify the current user and return user information.

    Args:
        current_user (User object): The current authenticated user.

    Returns:
        dict: A dictionary containing user information.
    """
    user_info = {
        "email": current_user.email,
        "firstname": current_user.firstname,
        "lastname": current_user.lastname,
        "access_role": current_user.access_role
    }
    return user_info




# @router.post("/logout",tags=["User Account Management"])
# async def sign_out(res: Response, current_user: User = Depends(get_current_user)):
#     if current_user:
#         res.delete_cookie("access_token")
#         return { "message": "Logout Successfully", "status_code": status.HTTP_200_OK}
#     else:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")




@router.put('/change-info',tags=["User Account Management"])
async def change_info(info_data: ChangeInfoUser, current_user: User = Depends(get_current_user)):
    """
    Changes the user's email, first name, and last name.

    Args:
        info_data (ChangeInfoUser): The data containing the new email, first name, and last name.
        current_user (User): The currently authenticated user.

    Returns:
        dict: A dictionary containing a success message.
    """
    # Check if the new email is already in use by another user
    db = SessionLocal()
    
    user_with_email = db.query(User).filter(User.email == info_data.email).first()
    db.close()
    if user_with_email and current_user.user_id != user_with_email.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already exist")

    # # Check if email is not modified
    # if info_data.email == "":
    #     info_data.email = current_user.email

    # Update user's information
    current_user.email = info_data.email
    current_user.firstname = info_data.firstname
    current_user.lastname = info_data.lastname

    # Save the updated user object to the database
    db = SessionLocal()
    db.add(current_user)
    db.commit()
    db.close()

    return {"message": "User information changed successfully","status_code": status.HTTP_200_OK}





@router.put('/change-password',tags=["User Account Management"])
async def change_password(change_password_data:ChangePasswordUser,current_user: User = Depends(get_current_user)):
    """
        Changes the user's password.

        Args:
            password_data (ChangePasswordUser): The data containing the current and new password.
            current_user (User): The currently authenticated user.

        Returns:
            dict: A dictionary containing a success message.
    """
    if not verify_password(change_password_data.current_password, current_user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    current_user.password = hash_password(change_password_data.new_password)
    db = SessionLocal()
    db.add(current_user)
    db.commit()
    db.close()
    return {"message": "Password changed successfully", "status_code": status.HTTP_200_OK}





@router.post('/forgot-password',tags=["User Account Management"])
async def forgot_password(request_email:SendToken, db: session = Depends(get_db)):
    user = db.query(User).filter(User.email == request_email.email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Email not found")   
        # Generate token
    
    
    token =  encode_email_token(request_email.email)
    sendEmail(receiver_email=request_email.email,token=token)
    save_token = ResetToken(user_id=user.user_id,token=token)
    db.add(save_token)
    db.commit()
    db.close()

    return {"message": "A token has been generated and sent to your email successfully!","status_code":200,"now":datetime.now()}


# @router.post('/verify_reset_token', tags=["Forgot Password"])
# async def verify(token_data: VerifyToken, db: session = Depends(get_db)):
#     # Check if the token exists in the database
#     token_exist = db.query(ResetToken).filter(ResetToken.token == token_data.token).first()
#     if not token_exist:
#         raise HTTPException(status_code=404, detail="Token not found")

#     # Check if the token has expired
#     current_time = datetime.now()
#     if token_exist.expire_date < current_time:
#         raise HTTPException(status_code=401, detail="Token has expired")

#     return {"valid": True, "status_code": status.HTTP_200_OK}

# @router.post('/send_email',tags=['Forgot Password'])
# async def send(reqForm:dict):
#     token = reqForm.get('token')
#     email = reqForm.get('received_email')
#     sendEmail(receiver_email=email,token=token)
#     return {'message': 'Email sent successfully',"status_code":status.HTTP_200_OK}

@router.put('/new-password',tags=["User Account Management"])
async def new_password(new_pwd: ResetNewPassword, db: session = Depends(get_db)):
    # Decode token to get email
    try:
        email = decode_email_token(new_pwd.token)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    # ตรวจสอบว่า token มีการใช้แล้วหรือไม่
    token_record = db.query(ResetToken).filter(ResetToken.token == new_pwd.token).first()
    if not token_record or token_record.expired_status == 1 or token_record.expire_date < datetime.now():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The password reset token is invalid or has expired. Please request a new one.")

    # เปลี่ยนรหัสผ่านใหม่ของผู้ใช้ในฐานข้อมูล
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Hash new password and update user's password
    user.password = hash_password(plain_password=new_pwd.new_password)
    db.commit()

    # Mark token as used
    token_record.expired_status = 1
    db.commit()

    return {"message": "Password has been reset!","status":200}
 