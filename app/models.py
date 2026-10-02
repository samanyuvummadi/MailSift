from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import enum

Base = declarative_base()

class CategoryEnum(str, enum.Enum):
    WORK = "Work"
    SCHOOL = "School"
    JOB_OPPORTUNITIES = "Job Opportunities"
    VERIFICATION_CODES = "Verification Codes"
    OTHER = "Other"

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    emails = relationship("Email", back_populates="user")

class Email(Base):
    __tablename__ = "emails"

    id = Column(String, primary_primary=True, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    sender = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    snippet = Column(String, nullable=False)
    category = Column(SQLEnum(CategoryEnum), nullable=False)
    rating = Column(Integer, default=3)
    reasoning = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="emails")
