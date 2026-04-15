from sqlalchemy import Column, Integer, String, VARCHAR, DateTime, Text
from datetime import datetime
from app_backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(VARCHAR(255), unique=True, index=True, nullable=False)
    password_hash = Column(VARCHAR(255), nullable=False)
    role = Column(String(50), default="citizen")
    credibility_score = Column(Integer, default=0)
    reset_token = Column(String, nullable=True)
    reset_token_expiry = Column(DateTime, nullable=True)
    profile_image = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

