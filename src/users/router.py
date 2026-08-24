from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from users.models import User
from users.schemas import UserCreateSchema
from users.auth import authenticate_user, create_access_token, get_password_hash

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session)
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Incorrect username or password",
            {"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/register", status_code=201)
async def register(user_data: UserCreateSchema, db: AsyncSession = Depends(get_session)):
    existing = await db.execute(select(User).where(User.username == user_data.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username, 
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        hashed_password=hashed
    )
    db.add(new_user)
    await db.commit()
    return {"msg": "User created"}
