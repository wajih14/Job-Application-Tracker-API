from collections.abc import AsyncGenerator

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime

DATABASE_URL = "sqlite+aiosqlite:///./test.db"

class Base(DeclarativeBase):
    pass

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company = Column(String, nullable=False)
    position = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner_id = Column(Integer, ForeignKey("Users.id", ondelete="CASCADE"), nullable=False)
    owner = relationship("User", back_populates="applications")

class User(Base):
    __tablename__ = "Users"

    id = Column(Integer,primary_key= True, autoincrement=True)
    email = Column(String, nullable = False, unique= True)
    hashed_password = Column(String, nullable = False)
    deleted_at = Column(DateTime, default = None)

    applications = relationship("Application", back_populates="owner")

engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)



async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session