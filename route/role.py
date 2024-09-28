from typing import List
from fastapi import APIRouter, Depends, HTTPException,status
from config.db_connect import get_db
from middleware.authentication import get_current_user
from model.user import User
from model.student import Student
from sqlalchemy.orm import Session

role_router = APIRouter()

@role_router.get('/student-all',response_model=List[Student],tags=['Admin Management'])
async def get_std(current_user: User = Depends(get_current_user),db: Session = Depends(get_db)):
    """
    Retrieves all student users.

    This route is accessible only to admin users.

    Args:
        current_user (User object): The currently authenticated user.

    Returns:
        List[User]: A list of all student users (if the current user is an admin).

    Raises:
        HTTPException: If the current user is not an admin or an error occurs.
    """

    if current_user.access_role != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    students = db.query(User).filter_by(access_role=0).all()  # Assuming access_role 0 is for students
    student_list = []
    for idx, student in enumerate(students, 1):
        student_list.append({
            'idx': idx,  # Use the index or any unique identifier
            'user_id': student.user_id,
            'author_name': f"{student.firstname} {student.lastname}",
            'email': student.email,
            'access_role': student.access_role
        })

    return student_list



@role_router.put('/change_role_student/{user_id}',tags=['Admin Management'])  ## user_id of student
async def change_role(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Changes the access role of a user.

    This route is accessible only to admin users.

    Args:
        user_id (int): The user ID of the user whose role is to be changed.
        new_role (int): The new role to assign to the user (0 for student, 1 for admin).
        current_user (User object): The currently authenticated user.
        db (Session): The database session.

    Returns:
        dict: A dictionary containing a success message.

    Raises:
        HTTPException: If the current user is not an admin, the user to change role does not exist, or an error occurs.
    """
    if current_user.access_role != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    # Query student user from database
    student = db.query(User).filter(User.user_id == user_id, User.access_role == 0).first()

    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student user not found")

    # Change role to admin
    student.access_role = 1
    db.commit()
    return {"message": "Role changed successfully","status_code":status.HTTP_200_OK}
