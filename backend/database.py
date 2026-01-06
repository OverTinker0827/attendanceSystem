"""
Database models and connection management for the attendance system.
Uses SQLAlchemy ORM with PostgreSQL.

New schema includes:
- Students: student info with class and embedding
- Classroom: classroom to IP mapping
- ClassSchedule: class schedule with time slots
- Attendance: attendance tracking by subject
"""

from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    DateTime,
    Time,
    Float,
    ARRAY,
    ForeignKey,
    UniqueConstraint,
    PrimaryKeyConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import config

# Create database engine
engine = create_engine(config.DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class Student(Base):
    """
    Students table - stores student information
    Fields match frontend expectations: student_id (usn), name, class, embedding
    """
    __tablename__ = "students"

    student_id = Column(String(20), primary_key=True)  # Frontend uses 'student_id' (USN)
    name = Column(String(255), nullable=True)
    class_name = Column(String(50), nullable=True)  # DB column for class
    embedding = Column(ARRAY(Float), nullable=True)  # Single embedding vector
    registered_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    attendance_records = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Student(student_id={self.student_id}, name={self.name}, class={self.class_name})>"


class Classroom(Base):
    """
    Classroom table - maps classroom to IP address
    """
    __tablename__ = "classroom"

    classroom = Column(String(50), primary_key=True)
    ip = Column(String(50), nullable=False)

    # Relationships
    schedules = relationship("ClassSchedule", back_populates="classroom_ref", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Classroom(classroom={self.classroom}, ip={self.ip})>"


class ClassSchedule(Base):
    """
    Class schedule table - defines when and where classes occur
    Composite primary key: (class_name, subject, start_time, end_time, classroom)
    """
    __tablename__ = "class_schedule"

    class_name = Column(String(50), nullable=False)
    subject = Column(String(100), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    classroom = Column(String(50), ForeignKey("classroom.classroom", ondelete="CASCADE"), nullable=False)

    # Relationships
    classroom_ref = relationship("Classroom", back_populates="schedules")

    # Composite primary key
    __table_args__ = (
        PrimaryKeyConstraint('class_name', 'subject', 'start_time', 'end_time', 'classroom'),
    )

    def __repr__(self):
        return f"<ClassSchedule(class={self.class_name}, subject={self.subject}, classroom={self.classroom})>"


class Attendance(Base):
    """
    Attendance table - tracks attendance percentage by student and subject
    Composite primary key: (student_id, subject)
    """
    __tablename__ = "attendance"

    student_id = Column(String(20), ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    subject = Column(String(100), nullable=False)
    attendance_percentage = Column(Float, nullable=False, default=0.0)
    last_marked_at = Column(DateTime, nullable=True)  # Track last attendance mark
    total_classes = Column(Integer, nullable=False, default=0)  # Track total classes
    attended_classes = Column(Integer, nullable=False, default=0)  # Track attended classes

    # Relationships
    student = relationship("Student", back_populates="attendance_records")

    # Composite primary key
    __table_args__ = (
        PrimaryKeyConstraint('student_id', 'subject'),
    )

    def __repr__(self):
        return f"<Attendance(student_id={self.student_id}, subject={self.subject}, percentage={self.attendance_percentage})>"


# Legacy tables for backward compatibility with existing frontend registration flow
class FaceEmbedding(Base):
    """
    LEGACY: Face embeddings table - kept for backward compatibility
    Registration API still stores multiple embeddings here
    """
    __tablename__ = "face_embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(20), ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    embedding_index = Column(Integer, nullable=False)
    embedding_vector = Column(ARRAY(Float), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("student_id", "embedding_index", name="uq_student_embedding_index"),
    )

    def __repr__(self):
        return f"<FaceEmbedding(student_id={self.student_id}, index={self.embedding_index})>"


def get_db():
    """
    Dependency function to get database session.
    Use in FastAPI route dependencies.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """
    Initialize database - create all tables.
    Run this during application startup or via separate script.
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


def drop_all_tables():
    """
    Drop all tables - USE WITH CAUTION!
    Only for development/testing.
    """
    Base.metadata.drop_all(bind=engine)
    print("⚠️ All database tables dropped")


if __name__ == "__main__":
    print("Initializing database...")
    init_database()