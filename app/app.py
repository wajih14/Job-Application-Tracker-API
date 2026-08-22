from typing import Literal
import uuid
from fastapi import FastAPI, HTTPException, Depends, Query
from app.schemas import AppSubmit, StatusUpdate, ApplicationResponse, ApplicationStatus
from app.db import Application, create_db_and_tables, get_async_session
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager




@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


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
async def delete_application(application_id: uuid.UUID, session: AsyncSession = Depends(get_async_session)):
    try:
        result = await session.execute(select(Application).where(Application.id == application_id))
        application = result.scalar_one_or_none()

        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        await session.delete(application)
        await session.commit()

        return application
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/applications/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: uuid.UUID,
    new_application: AppSubmit,
    session: AsyncSession = Depends(get_async_session)
):
    try:
        result = await session.execute(select(Application).where(Application.id == application_id))
        application = result.scalar_one_or_none()

        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        application.company = new_application.company
        application.position = new_application.position
        application.status = new_application.status
        await session.commit()
        return application
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/applications/{application_id}", response_model=ApplicationResponse)
async def update_application_status(
    application_id: uuid.UUID,
    new_status: StatusUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    try:

        result = await session.execute(select(Application).where(Application.id == application_id))
        application = result.scalar_one_or_none()

        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        application.status = new_status.status
        await session.commit()
        return application
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/applications/", response_model=list[ApplicationResponse])
async def get_applications(
    status: ApplicationStatus | None = None,
    company: str | None = None, 
    position: str | None = None,
    sort: Literal["newest", "oldest"] | None = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session)):
    try:
        query = select(Application)
        if status is not None:
            query = query.where(Application.status == status)
        if company is not None:
            query = query.where(Application.company == company)
        if position is not None:
            query = query.where(Application.position == position)
        if sort is not None:
            if sort == "newest":
                query = query.order_by(Application.created_at.desc())
            elif sort == "oldest":
                query = query.order_by(Application.created_at.asc())

        query = query.offset(offset).limit(limit)
        
        result = await session.execute(query)
        applications = result.scalars().all()

        return applications
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

