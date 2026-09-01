from datetime import datetime, timedelta, timezone
from typing import Literal, Annotated
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from jwt import InvalidTokenError
from app.schemas import AppSubmit, StatusUpdate, ApplicationResponse, ApplicationStatus, UserResponse, UserSubmit, Token
from app.db import Application, get_async_session, User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pwdlib import PasswordHash
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user")


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        session: AsyncSession = Depends(get_async_session)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code= 401, detail="Unauthorized")
        if not user_id.isdigit():
            raise HTTPException(status_code= 401, detail="Unauthorized")
        user_id = int(user_id)
    except InvalidTokenError:
        raise HTTPException(status_code= 401, detail="Unauthorized")

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user
    
    



app = FastAPI()


@app.post("/applications", response_model=ApplicationResponse)
async def create_application(
    application: AppSubmit,
    session: AsyncSession = Depends(get_async_session)
):
    new_application = Application(
        company=application.company,
        position=application.position,
        status=application.status
    )
    session.add(new_application)
    await session.commit()
    await session.refresh(new_application)
    return new_application


@app.delete("/applications/{application_id}", response_model=ApplicationResponse)
async def delete_application(
    application_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(Application).where(Application.id == application_id))
    application = result.scalar_one_or_none()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    await session.delete(application)
    await session.commit()

    return application

@app.put("/applications/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: int,
    new_application: AppSubmit,
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(Application).where(Application.id == application_id))
    application = result.scalar_one_or_none()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    application.company = new_application.company
    application.position = new_application.position
    application.status = new_application.status
    await session.commit()
    return application


@app.patch("/applications/{application_id}", response_model=ApplicationResponse)
async def update_application_status(
    application_id: int,
    new_status: StatusUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(Application).where(Application.id == application_id))
    application = result.scalar_one_or_none()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    application.status = new_status.status
    await session.commit()
    return application


@app.get("/applications/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: int, 
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(Application).where(Application.id == application_id))
    application = result.scalar_one_or_none()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    return application

@app.get("/applications", response_model=list[ApplicationResponse])
async def get_applications(
    status: ApplicationStatus | None = None,
    company: str | None = None, 
    position: str | None = None,
    sort: Literal["newest", "oldest"] = "newest",
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session)):
    query = select(Application)
    if status is not None:
        query = query.where(Application.status == status)
    if company is not None:
        query = query.where(Application.company == company)
    if position is not None:
        query = query.where(Application.position == position)
    if sort == "newest":
        query = query.order_by(Application.created_at.desc())
    elif sort == "oldest":
        query = query.order_by(Application.created_at.asc())

    query = query.offset(offset).limit(limit)
        
    result = await session.execute(query)
    applications = result.scalars().all()

    return applications

@app.post("/user", response_model = Token)
async def login_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSession = Depends(get_async_session)
):
    if not form_data.username.isdigit():
        raise HTTPException(status_code=401, detail="Unauthorized")
    query = await session.execute(select(User).where(User.id == int(form_data.username)))
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

@app.post("/users", response_model = UserResponse)
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

@app.get("/users/me",response_model=UserResponse)
async def user_me(
    current_user : Annotated[User, Depends(get_current_user)]
):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        logged_in=True
    )
