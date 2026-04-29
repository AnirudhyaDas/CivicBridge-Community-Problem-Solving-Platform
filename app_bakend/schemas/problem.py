from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProblemCreate(BaseModel):
    title: str
    description: str
    category: str
    location: str
    severity: str

class ProblemOut(BaseModel):
    id: int
    title: str
    description: str
    category: str
    location: str
    severity: str
    status: str
    before_image_path: Optional[str] = None
    created_by: int
    created_at: Optional[datetime] = None  # Add this

    class Config:
        from_attributes = True