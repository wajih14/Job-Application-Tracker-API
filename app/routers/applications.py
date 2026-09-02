from fastapi import APIRouter, HTTPException, Depends, Query

from typing import Literal, Annotated

from app.schemas import AppSubmit, StatusUpdate, ApplicationResponse, ApplicationStatus

from app.db import Application, get_async_session, User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user



router = APIRouter()

@router.post("", response_model=ApplicationResponse)
async def create_application(
    application: AppSubmit,
    current_user : Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session)
):
    new_application = Application(
        company=application.company,
        position=application.position,
        status=application.status,
    )
    new_application.owner = current_user
    session.add(new_application)
    await session.commit()
    await session.refresh(new_application)
    return new_application


@router.delete("/{application_id}", response_model=ApplicationResponse)
async def delete_application(
    current_user : Annotated[User, Depends(get_current_user)],
    application_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(Application).where(Application.id == application_id).where(Application.owner_id == current_user.id))
    application = result.scalar_one_or_none()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    await session.delete(application)
    await session.commit()

    return application

@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    current_user : Annotated[User, Depends(get_current_user)],
    application_id: int,
    new_application: AppSubmit,
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(Application).where(Application.id == application_id).where(Application.owner_id == current_user.id))
    application = result.scalar_one_or_none()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    application.company = new_application.company
    application.position = new_application.position
    application.status = new_application.status
    await session.commit()
    return application


@router.patch("/{application_id}", response_model=ApplicationResponse)
async def update_application_status(
    current_user : Annotated[User, Depends(get_current_user)],
    application_id: int,
    new_status: StatusUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(Application).where(Application.id == application_id).where(Application.owner_id == current_user.id))
    application = result.scalar_one_or_none()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    application.status = new_status.status
    await session.commit()
    return application


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    current_user : Annotated[User, Depends(get_current_user)],
    application_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(Application).where(Application.id == application_id).where(Application.owner_id == current_user.id))
    application = result.scalar_one_or_none()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    return application

@router.get("", response_model=list[ApplicationResponse])
async def get_applications(
    current_user : Annotated[User, Depends(get_current_user)],
    status: ApplicationStatus | None = None,
    company: str | None = None, 
    position: str | None = None,
    sort: Literal["newest", "oldest"] = "newest",
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session)):
    query = select(Application).where(Application.owner_id == current_user.id)
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