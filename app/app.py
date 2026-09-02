from fastapi import FastAPI
from app.routers import applications, users

app = FastAPI()

app.include_router(applications.router, prefix="/applications", tags=["Applications"])
app.include_router(users.router, prefix="/users", tags=["Users"])

