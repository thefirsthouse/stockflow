from pydantic import BaseModel, EmailStr, Field


class UserCreateSchema(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    password: str = Field(..., min_length=8)
