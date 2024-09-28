from pydantic import BaseModel

class Student(BaseModel):
    idx: int
    user_id: int
    author_name: str
    email: str
    access_role: int
