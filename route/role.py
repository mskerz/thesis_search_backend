from typing import List
from fastapi import APIRouter, Depends, HTTPException,status
from config.db_connect import get_db
from middleware.authentication import get_current_user
from model.advisor import Advisor
from model.thesis import ThesisFormRequest,ThesisDocument
from model.user import Admin, RegisterUser, User
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

    students = db.query(User).filter(User.access_role != 1).all()  # Assuming access_role 0 is for students
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



@role_router.put('/user/change-permission/{user_id}/role/{role}',tags=['Admin Management'])  ## user_id of student
async def change_role(user_id: int,role:int ,current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Changes the access role of a user.

    This route is accessible only to admin users.

    Args:
        user_id (int): The user ID of the user whose role is to be changed.
        new_role (int): The new role to assign to the user (0 for student, 2 for old nisit).
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
    student.access_role = role
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
    advisor = db.query(Advisor).filter(Advisor.advisor_id ==thesis.advisor_id).first()
    if not thesis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thesis not found") 
    
    return {"doc_id": thesis.doc_id,"title_th":thesis.title_th,"title_en":thesis.title_en,"advisor_id":thesis.advisor_id,"advisor_name":advisor.advisor_name ,"year":thesis.year}

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





@role_router.get('/admin-all',response_model=List[Admin],tags=['Admin Management'])
async def get_admin(current_user: User = Depends(get_current_user),db: Session = Depends(get_db)):
    """
    Retrieves all admin users.

    This route is accessible only to admin users.

    Args:
        current_user (User object): The currently authenticated user.

    Returns:
        List[User]: A list of all admin users (if the current user is an admin).

    Raises:
        HTTPException: If the current user is not an admin or an error occurs.
    """

    if current_user.access_role != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    admin_all = db.query(User).filter(User.access_role == 1, User.user_id != current_user.user_id).all()  # Assuming access_role 0 is for students
    admin_list = []
    for idx, admin in enumerate(admin_all, 1):
        admin_list.append({
            'idx': idx,  # Use the index or any unique identifier
            'user_id': admin.user_id,
            'fullname': f"{admin.firstname} {admin.lastname}",
            'email': admin.email,
            'access_role': admin.access_role
        }) 

    return admin_list

@role_router.post('/admin/add', tags=['Admin Management'])
async def add_admin(admin_data: RegisterUser, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Adds a new admin user.

    This route is accessible only to admin users.

    Args:
        admin_data (AdminCreate): The data for the new admin user.
        current_user (User object): The currently authenticated user.

    Returns:
        Admin: The created admin user.

    Raises:
        HTTPException: If the current user is not an admin or an error occurs.
    """

    if current_user.access_role != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    # ตรวจสอบว่าอีเมลนี้มีอยู่แล้วหรือไม่
    existing_user = db.query(User).filter(User.email == admin_data.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")



    # ตรวจสอบว่ามี admin อยู่แล้วหรือไม่
    new_admin = User(
        firstname=admin_data.firstname,
        lastname=admin_data.lastname,
        email=admin_data.email,
        password=admin_data.password,  # คุณควรจะทำการเข้ารหัสรหัสผ่านก่อน
        access_role=1  # ตั้งค่า access_role ให้เป็น admin
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return {"message":"เพิ่มผู้ดูแลระบบสำเร็จ","status":200,"last_user_id":new_admin.user_id}




@role_router.delete('/admin/delete/{user_id}', tags=['Admin Management'])
async def delete_admin(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Deletes an admin user.

    This route is accessible only to admin users.

    Args:
        user_id (int): The ID of the admin user to be deleted.
        current_user (User object): The currently authenticated user.

    Raises:
        HTTPException: If the current user is not an admin or an error occurs.
    """

    # ตรวจสอบว่า current_user เป็น admin หรือไม่
    if current_user.access_role != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    # ค้นหาผู้ใช้ที่ต้องการลบ
    admin_to_delete = db.query(User).filter(User.user_id == user_id).first()
    if not admin_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin user not found")

    # ลบผู้ใช้
    db.delete(admin_to_delete)
    db.commit()

    return {"message": "ลบผู้ดูแลระบบสำเร็จ", "status": 200}



@role_router.get('/admin/dashboard', tags=['Admin Management'])
async def admin_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ""
    # ตรวจสอบว่า current_user เป็น admin หรือไม่
    if current_user.access_role != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    
    result ={}
    student_count = db.query(User).filter(User.access_role==0).count()
    alumni_count =db.query(User).filter(User.access_role==2).count()
    admin_count = db.query(User).filter(User.access_role==1).count()
    doc_count = db.query(ThesisDocument).filter(ThesisDocument.deleted_at==None).count()
    doc_waiting_count =db.query(ThesisDocument).filter(ThesisDocument.recheck_status==0).count()
    doc_approved_count =db.query(ThesisDocument).filter(ThesisDocument.recheck_status==1).count()
    doc_rejected_count =db.query(ThesisDocument).filter(ThesisDocument.recheck_status==2).count()
    advisor_count = db.query(Advisor).count()
        # เพิ่มข้อมูลลงใน result
    result['student_count'] = student_count
    result['alumni_count'] = alumni_count
    result['admin_count'] = admin_count        
    result['doc_count'] = doc_count

    result['doc_waiting_count'] = doc_waiting_count
    result['doc_approved_count'] = doc_approved_count
    result['doc_rejected_count'] = doc_rejected_count
    result['advisor_count'] = advisor_count

    return result
