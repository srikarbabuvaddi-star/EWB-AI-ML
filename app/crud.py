"""Database CRUD repository operations for student records."""

import logging
from typing import List, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Student
from app.schemas import StudentCreate, StudentUpdatePut, StudentUpdatePatch
from app.exceptions import (
    StudentNotFoundError,
    EmailAlreadyExistsError,
    DatabaseOperationError,
)

logger = logging.getLogger(__name__)


def get_student_by_id(db: Session, student_id: int) -> Optional[Student]:
    """Retrieve a single student record by primary key ID."""
    return db.query(Student).filter(Student.id == student_id).first()


def get_student_by_email(db: Session, email: str) -> Optional[Student]:
    """Retrieve a single student record by email address (case-insensitive)."""
    return db.query(Student).filter(func.lower(Student.email) == email.lower()).first()


def get_students(
    db: Session,
    name: Optional[str] = None,
    course: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
) -> Tuple[List[Student], int]:
    """List students with optional search by name, filter by course, and pagination.

    Returns:
        Tuple[List[Student], int]: A tuple containing the list of matching students and the total count.
    """
    query = db.query(Student)

    if name and name.strip():
        search_pattern = f"%{name.strip()}%"
        query = query.filter(Student.name.ilike(search_pattern))

    if course and course.strip():
        course_pattern = f"%{course.strip()}%"
        query = query.filter(Student.course.ilike(course_pattern))

    total_count = query.count()
    students = (
        query.order_by(Student.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return students, total_count


def create_student(db: Session, student_in: StudentCreate) -> Student:
    """Create a new student record.

    Validates email uniqueness and handles database errors safely.
    """
    # Proactive uniqueness check
    existing = get_student_by_email(db, student_in.email)
    if existing:
        raise EmailAlreadyExistsError(student_in.email)

    db_student = Student(
        name=student_in.name,
        date_of_birth=student_in.date_of_birth,
        email=student_in.email,
        phone=student_in.phone,
        course=student_in.course,
        address=student_in.address,
        enrollment_date=student_in.enrollment_date,
    )

    try:
        db.add(db_student)
        db.commit()
        db.refresh(db_student)
        return db_student
    except IntegrityError as exc:
        db.rollback()
        logger.warning("Integrity error creating student: %s", exc)
        raise EmailAlreadyExistsError(student_in.email) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Database error creating student: %s", exc, exc_info=True)
        raise DatabaseOperationError("Database failure while creating student record.") from exc


def update_student_put(
    db: Session,
    student_id: int,
    student_in: StudentUpdatePut,
) -> Student:
    """Full update/replacement of student details (PUT).

    Requires all editable fields and validates email uniqueness.
    """
    db_student = get_student_by_id(db, student_id)
    if not db_student:
        raise StudentNotFoundError(student_id)

    # If email changed, check conflict
    if db_student.email.lower() != student_in.email.lower():
        existing = get_student_by_email(db, student_in.email)
        if existing and existing.id != student_id:
            raise EmailAlreadyExistsError(student_in.email)

    db_student.name = student_in.name
    db_student.date_of_birth = student_in.date_of_birth
    db_student.email = student_in.email
    db_student.phone = student_in.phone
    db_student.course = student_in.course
    db_student.address = student_in.address
    db_student.enrollment_date = student_in.enrollment_date

    try:
        db.commit()
        db.refresh(db_student)
        return db_student
    except IntegrityError as exc:
        db.rollback()
        logger.warning("Integrity error updating student (PUT): %s", exc)
        raise EmailAlreadyExistsError(student_in.email) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Database error updating student (PUT): %s", exc, exc_info=True)
        raise DatabaseOperationError("Database failure while updating student record.") from exc


def update_student_patch(
    db: Session,
    student_id: int,
    student_in: StudentUpdatePatch,
) -> Student:
    """Partial update of student details (PATCH).

    Only fields explicitly provided in the request payload will be modified.
    """
    db_student = get_student_by_id(db, student_id)
    if not db_student:
        raise StudentNotFoundError(student_id)

    update_data = student_in.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"]:
        new_email = update_data["email"]
        if db_student.email.lower() != new_email.lower():
            existing = get_student_by_email(db, new_email)
            if existing and existing.id != student_id:
                raise EmailAlreadyExistsError(new_email)

    for field, value in update_data.items():
        setattr(db_student, field, value)

    try:
        db.commit()
        db.refresh(db_student)
        return db_student
    except IntegrityError as exc:
        db.rollback()
        logger.warning("Integrity error updating student (PATCH): %s", exc)
        raise EmailAlreadyExistsError(update_data.get("email", "")) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Database error updating student (PATCH): %s", exc, exc_info=True)
        raise DatabaseOperationError("Database failure while updating student record.") from exc


def delete_student(db: Session, student_id: int) -> None:
    """Delete a student record by ID."""
    db_student = get_student_by_id(db, student_id)
    if not db_student:
        raise StudentNotFoundError(student_id)

    try:
        db.delete(db_student)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Database error deleting student: %s", exc, exc_info=True)
        raise DatabaseOperationError("Database failure while deleting student record.") from exc
