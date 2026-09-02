from typing import Annotated
from datetime import timedelta

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.auth import (
    get_current_user,
    password_hash,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db import get_async_session, User

from app.schemas import UserResponse, UserSubmit, Token



router = APIRouter()


@router.post("/login", response_model = Token)
async def login_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSession = Depends(get_async_session)
):
    query = await session.execute(select(User).where(User.email == form_data.username))
    user = query.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if password_hash.verify(form_data.password, user.hashed_password):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            {"sub": str(user.id)},
            access_token_expires)
        return Token(access_token=access_token, token_type="bearer")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.post("", response_model = UserResponse)
async def create_user(
    user: UserSubmit,
    session: AsyncSession = Depends(get_async_session)
):
    new_user = User(
        email = user.email,
        hashed_password = password_hash.hash(user.password)
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return UserResponse(
            id= new_user.id,
            email= new_user.email,
            logged_in= False
        )

@router.get("/me",response_model=UserResponse)
async def user_me(
    current_user : Annotated[User, Depends(get_current_user)]
):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        logged_in=True
    )



