from sqlalchemy import Column, String, Integer, DateTime, Boolean, Date, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, ARRAY, REAL
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.database import Base
import uuid
import datetime

# Helper to handle UUID type difference between Postgres and SQLite
from sqlalchemy.types import TypeDecorator, CHAR    

class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(32), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value

class User(Base):
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(Text, nullable=False)
    
    profile_image_s3_key = Column(Text)
    profile_prompt = Column(Text)
    
    status = Column(String(20), default='active', nullable=False)
    
    failed_login_count = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    last_login_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True))

    diaries = relationship("Diary", back_populates="user", cascade="all, delete-orphan")


class Diary(Base):
    __tablename__ = "diaries"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    diary_date = Column(Date, nullable=False)
    content = Column(Text, nullable=False)
    content_embedding = Column(JSON, nullable=True) # Used for simple vector search
    image_s3_key = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="diaries")
    chunks = relationship("DiaryChunk", back_populates="diary", cascade="all, delete-orphan")

# Note: Vector type is specific to pgvector. For SQLite compatibility, we might need a workaround or omit embedding logic if using SQLite.
# For now, defining the structure.

class DiaryChunk(Base):
    __tablename__ = "diary_chunks"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    diary_id = Column(GUID(), ForeignKey("diaries.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    
    token_count = Column(Integer)
    start_char = Column(Integer)
    end_char = Column(Integer)
    
    embedding_status = Column(String(20), default='pending')
    last_embedded_at = Column(DateTime(timezone=True))
    
    metadata_ = Column("metadata", JSON, nullable=True) # Renamed to avoid reserved keyword conflict if any, but `metadata` is okay usually. map to JSON for SQLite compatibility

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    diary = relationship("Diary", back_populates="chunks")
