from typing import List
from fastapi import APIRouter, Depends, HTTPException,status
from config.db_connect import get_db
from middleware.authentication import get_current_user
from model.thesis import ThesisFormRequest,ThesisDocument
from model.user import User
from model.student import Student
from sqlalchemy.orm import Session
from datetime import datetime
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



@role_router.put('/user/change-permission/{user_id}',tags=['Admin Management'])  ## user_id of student
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


@role_router.get('/thesis/id/{doc_id}',tags=['Admin Management'])
async def get_thesis_one(doc_id:int,current_user:User= Depends(get_current_user), db: Session = Depends(get_db)):
    """
    get one thesis upload
    """
    if current_user.access_role != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        # Fetch the existing thesis entry from the database
    thesis = db.query(ThesisDocument).filter(ThesisDocument.doc_id == doc_id).first()
    if not thesis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thesis not found")
    
    return {"doc_id": thesis.doc_id,"title_th":thesis.title_th,"title_en":thesis.title_en,"advisor_id":thesis.advisor_id,"year":thesis.year}

@role_router.put('/thesis/edit/{doc_id}',tags=['Admin Management'])
async def edit_thesis(doc_id:int,thesis_Edit:ThesisFormRequest,current_user:User = Depends(get_current_user),  db: Session = Depends(get_db)):
    """Edit"""
    if current_user.access_role != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    
    # Fetch the existing thesis entry from the database
    thesis = db.query(ThesisDocument).filter(ThesisDocument.doc_id == doc_id).first()
    if not thesis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thesis not found")
    
    # Update the thesis fields with the new data if it's not empty, otherwise use the current value
    thesis.title_th = thesis_Edit.title_th if thesis_Edit.title_th.strip() else thesis.title_th
    thesis.title_en = thesis_Edit.title_en if thesis_Edit.title_en.strip() else thesis.title_en
    thesis.advisor_id = thesis_Edit.advisor_id if thesis_Edit.advisor_id else thesis.advisor_id
    thesis.year = thesis_Edit.year if thesis_Edit.year else thesis.year
    
    # Commit the changes to the database
    db.commit()
    return {"message": "Thesis updated successfully", "status": 200}



@role_router.post('/thesis/delete/{doc_id}', tags=['Admin Management'])
async def delete_thesis(doc_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete"""
    # Check if the current user has admin access
    if current_user.access_role != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    
    try:
        # Fetch the existing thesis entry from the database
        thesis = db.query(ThesisDocument).filter(ThesisDocument.doc_id == doc_id).first()
        
        if not thesis:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thesis not found")
        
        # Delete the thesis
        thesis.deleted_at = datetime.now();
        
        # Commit the changes to the database
        db.commit()
        
        return {"message": "Thesis deleted successfully"}
    
    except Exception as e:
        # Log the error for debugging (optional)
        print(f"Error occurred while deleting thesis: {str(e)}")
        
        # Raise a 500 Internal Server Error with a generic message
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while deleting the thesis")
