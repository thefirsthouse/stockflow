from pydantic import BaseModel


class UserCreateSchema(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str