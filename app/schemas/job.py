from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.schemas.transaction import JobSummaryResponse

class JobBase(BaseModel):
    filename: str

class JobCreate(JobBase):
    pass

class JobResponse(JobBase):
    id: int
    status: str
    row_count_raw: Optional[int] = None
    row_count_clean: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class JobUploadResponse(BaseModel):
    job_id: int

class JobStatusResponse(JobResponse):
    summary: Optional[JobSummaryResponse] = None
