from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from app_backend.database import Base

class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, index=True)
    before_image_path = Column(String, nullable=True)
    title = Column(String)
    description = Column(Text)
    category = Column(String)
    location = Column(String)
    severity = Column(String)
    status = Column(String, default="open")
    created_by = Column(Integer, ForeignKey("users.id"))

