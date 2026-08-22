import uuid
from fastapi import FastAPI, HTTPException, Depends
from app.schemas import AppSubmit, StatusUpdate
from app.db import Application, create_db_and_tables, get_async_session
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager



@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/applications")
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

@app.get("/applications")
async def get_applications(
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(Application).order_by(Application.created_at.desc()))
    applications = [row[0] for row in result.all()]

    applications_list = []
    for application in applications:
        applications_list.append({
            "id": str(application.id),
            "company": application.company,
            "position": application.position,
            "status": application.status,
            "created_at": application.created_at.isoformat()
        })
    return {"applications": applications_list}


@app.delete("/applications/{application_id}")
async def delete_application(application_id: str, session: AsyncSession = Depends(get_async_session)):
    try:
        post_uuid = uuid.UUID(application_id)

        result = await session.execute(select(Application).where(Application.id == post_uuid))
        application = result.scalar_one_or_none()

        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        await session.delete(application)
        await session.commit()

        return {"message": "Application deleted"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/applications/{application_id}")
async def update_application(
    application_id: str,
    new_application: AppSubmit,
    session: AsyncSession = Depends(get_async_session)
):
    try:
        post_uuid = uuid.UUID(application_id)
    
        result = await session.execute(select(Application).where(Application.id == post_uuid))
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


@app.patch("/applications/{application_id}")
async def update_application_status(
    application_id: str,
    new_status: StatusUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    try:
        post_uuid = uuid.UUID(application_id)

        result = await session.execute(select(Application).where(Application.id == post_uuid))
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


@app.get("/applications/")
async def get_applications(
    status: str | None = None,
    company: str | None = None, 
    position: str | None = None,
    sort: str| None = None,
    limit: int | None = None,
    offset: int | None = None,
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

        if offset is not None:
            query = query.offset(offset)

        if limit is not None:
            query = query.limit(limit)
        
        result = await session.execute(query)
        applications = result.scalars().all()

        applications_list = []
        for application in applications:
            applications_list.append({
                "id": str(application.id),
                "company": application.company,
                "position": application.position,
                "status": application.status,
                "created_at": application.created_at.isoformat()
            })
        return {"applications": applications_list}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

