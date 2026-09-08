from pydantic import BaseModel
from typing import Optional
from datetime import date

class StandardBase(BaseModel):
    standard_number: str
    title: str
    description: Optional[str] = None
    ai_summary: Optional[str] = None
    publication_date: Optional[date] = None
    latest_version: Optional[str] = None
    mandatory_certification: Optional[str] = None
    download_link: Optional[str] = None
    is_active: bool = True

class StandardCreate(StandardBase):
    id: str

class Standard(StandardBase):
    id: str

    class Config:
        from_attributes = True
