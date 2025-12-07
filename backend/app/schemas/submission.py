from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class SubmissionCreate(BaseModel):
    title: str
    content_type: str  # html, markdown, pdf, docx
    original_content: Optional[str] = None


class SubmissionResponse(BaseModel):
    id: uuid.UUID
    title: str
    content_type: str
    status: str
    submitted_at: datetime
    submitted_by: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


class SubmissionAnalyzeRequest(BaseModel):
    pass  # No body needed, just trigger


class SubmissionAnalyzeResponse(BaseModel):
    message: str
    submission_id: uuid.UUID
