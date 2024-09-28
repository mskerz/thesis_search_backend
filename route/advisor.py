from typing import List
from fastapi import APIRouter, Depends, HTTPException,status
from pydantic import ValidationError
from config.db_connect import Session, get_db
from model.advisor import AdvisorForm, Advisors,Advisor
from middleware.authentication import get_current_user
from model.user import User

advisor_router = APIRouter()

@advisor_router.get('/advisors-all')


@advisor_router.get('/advisors',response_model=List[Advisors],tags=['Admin Management'])
async def get_advisor(current_user: User = Depends(get_current_user),db: Session = Depends(get_db)):
    """
    Retrieves all advisor.

    Args:
        current_user (User object): The currently authenticated user.

    Returns:
        List[Advisors]: A list of all student users (if the current user is an admin).

    Raises:
        HTTPException: If the current user is not an admin or an error occurs.
    """

    if not current_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    advisor = db.query(Advisor).all() # Assuming access_role 0 is for students
    
 
    return advisor

@advisor_router.get('/advisors/{advisor_id}', response_model=Advisors, tags=['Admin Management'])
async def get_advisor_one(advisor_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
  """
  Retrieves a specific advisor by ID.

  Args:
    advisor_id (int): The ID of the advisor to retrieve.
    current_user (User object): The currently authenticated user.

  Returns:
    Advisor: The advisor object with the specified ID (if found and user has permission).

  Raises:
    HTTPException: If the current user is not authorized or the advisor is not found.
  """

  if current_user.access_role != 1:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

  advisor = db.query(Advisor).filter(Advisor.advisor_id == advisor_id).first()

  if not advisor:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Advisor not found")

  return advisor





@advisor_router.post('/advisor/new',tags=['Admin Management'])
async def new_advisor(new_advisor: AdvisorForm,current_user: User = Depends(get_current_user),db: Session = Depends(get_db)):
    
    if current_user.access_role != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    try:
        new_advisor = Advisor(advisor_name=new_advisor.advisor_name)
        db.add(new_advisor)
        db.commit()
        return {"message": "The advisor has been created successfully","status_code":200}

    except ValidationError as e :
        raise HTTPException(status_code=400, detail=str(e))
    


@advisor_router.put('/advisor/edit/{advisor_id}',tags=['Admin Management'])
async def update_advisor(advisor_id: int, update_advisor: AdvisorForm, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    
    if current_user.access_role != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    edit_advisor = db.query(Advisor).filter(Advisor.advisor_id == advisor_id).first()
    if not edit_advisor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Advisor not found")

    edit_advisor.advisor_name = update_advisor.advisor_name
    db.add(edit_advisor)
    db.commit()
    return {"message": "This advisor has been updated !"}


@advisor_router.delete('/advisor/delete/{advisor_id}',tags=['Admin Management'])
async def delete_advisor(advisor_id:int,current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.access_role != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    this_advisor = db.query(Advisor).filter(Advisor.advisor_id==advisor_id).first()
    if not this_advisor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Advisor not found")
    try:
        db.delete(this_advisor)
        db.commit()
        return {"message": "This advisor has been deleted !"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}") 

    