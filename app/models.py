"""SQLAlchemy ORM models for student records."""

from sqlalchemy import Column, Integer, String, Date, Text, DateTime, func
from app.database import Base


class Student(Base):
    """Student ORM model representing the `students` table.

    Enforces primary key, required fields, and unique email constraint at the database layer.
    """

    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    date_of_birth = Column(Date, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(25), nullable=True)
    course = Column(String(100), nullable=True, index=True)
    address = Column(Text, nullable=True)
    enrollment_date = Column(Date, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<Student(id={self.id}, name='{self.name}', email='{self.email}', "
            f"course='{self.course}')>"
        )
