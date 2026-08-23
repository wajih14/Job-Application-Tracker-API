from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from uuid import UUID
from datetime import datetime

class ApplicationStatus(str, Enum):
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFERED = "offered"
    REJECTED = "rejected"
    ACCEPTED = "accepted"
    SEEKING_TO_APPLY = "seeking to apply"
    SPECIAL = "special"

class AppSubmit(BaseModel):
    company: str = Field(min_length=2, description="The name of the company")
    position: str = Field(min_length=2, description="The position applied for")
    status: ApplicationStatus

class StatusUpdate(BaseModel):
    status: ApplicationStatus

class ApplicationResponse(BaseModel):
    id: int
    company: str
    position: str
    status: ApplicationStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)