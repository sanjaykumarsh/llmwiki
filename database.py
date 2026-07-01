import os
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from passlib.context import CryptContext
import enum

# Database setup
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./llmwiki.db")

if DATABASE_URL.startswith("sqlite:///") and ":memory:" not in DATABASE_URL:
    sqlite_path = DATABASE_URL.replace("sqlite:///", "", 1)
    Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
# Use pbkdf2_sha256 as default for broad compatibility in container builds,
# while keeping bcrypt for backward verification of existing hashes.
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


class PermissionLevel(str, enum.Enum):
    """Permission levels for project sharing"""
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    projects = relationship("Project", back_populates="owner", foreign_keys="Project.owner_id")
    memberships = relationship("ProjectMembership", back_populates="user")
    
    def verify_password(self, plain_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, self.password_hash)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)


class Project(Base):
    """Project/Wiki model"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="projects", foreign_keys=[owner_id])
    wiki_pages = relationship("WikiPage", back_populates="project", cascade="all, delete-orphan")
    raw_documents = relationship("RawDocument", back_populates="project", cascade="all, delete-orphan")
    memberships = relationship("ProjectMembership", back_populates="project", cascade="all, delete-orphan")


class ProjectMembership(Base):
    """Project membership/sharing model"""
    __tablename__ = "project_memberships"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    permission_level = Column(Enum(PermissionLevel), default=PermissionLevel.READ_ONLY, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="memberships")
    user = relationship("User", back_populates="memberships")


class WikiPage(Base):
    """Wiki page model"""
    __tablename__ = "wiki_pages"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    filename = Column(String, nullable=False)
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="wiki_pages")


class RawDocument(Base):
    """Raw source document model"""
    __tablename__ = "raw_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    filename = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    size = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="raw_documents")


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
