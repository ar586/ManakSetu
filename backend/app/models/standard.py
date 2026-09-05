from sqlalchemy import Column, String, Text, Date, Boolean
from app.models.base import Base

class Standard(Base):
    __tablename__ = "standards"

    id = Column(String, primary_key=True, index=True) # e.g. IS 1234:2020
    standard_number = Column(String, index=True, nullable=False) # e.g. IS 1234
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    publication_date = Column(Date, nullable=True)
    latest_version = Column(String, nullable=True)
    mandatory_certification = Column(String, nullable=True) # e.g. BIS, CRS, Hallmarking
    is_active = Column(Boolean, default=True)
