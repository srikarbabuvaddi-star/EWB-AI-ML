"""FastAPI router for Student CRUD operations."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.schemas import (
    StudentCreate,
    StudentUpdatePut,
    StudentUpdatePatch,
    StudentResponse,
)
from app.crud import (
    create_student,
    get_students,
    get_student_by_id,
    update_student_put,
    update_student_patch,
    delete_student,
)
from app.exceptions import (
    StudentNotFoundError,
    EmailAlreadyExistsError,
    DatabaseOperationError,
)

router = APIRouter(prefix="/students", tags=["Students"])


@router.post(
    "",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create student record",
    description="Registers a new student record after validating required fields and email uniqueness.",
)
def create_student_endpoint(
    student_in: StudentCreate,
    db: Session = Depends(get_db),
) -> StudentResponse:
    """Create a new student record and return HTTP 201."""
    try:
        return create_student(db=db, student_in=student_in)
    except EmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while creating the student.",
        ) from exc


@router.get(
    "",
    response_model=List[StudentResponse],
    status_code=status.HTTP_200_OK,
    summary="List and filter students",
    description=(
        "Retrieve a paginated list of students. Supports search by student name "
        "and filtering by course. Returns total count in `X-Total-Count` header."
    ),
)
def list_students_endpoint(
    response: Response,
    search: Optional[str] = Query(None, description="Search term for student name (case-insensitive)"),
    name: Optional[str] = Query(None, description="Alternate parameter for student name search"),
    course: Optional[str] = Query(None, description="Filter by course name"),
    limit: int = Query(
        settings.DEFAULT_PAGE_LIMIT,
        ge=1,
        le=settings.MAX_PAGE_LIMIT,
        description="Maximum number of records to return",
    ),
    offset: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    skip: Optional[int] = Query(None, ge=0, description="Alternative alias for offset"),
    db: Session = Depends(get_db),
) -> List[StudentResponse]:
    """Retrieve students with search, course filtering, and pagination."""
    # Resolve search query alias
    query_name = search if search is not None else name

    # Resolve offset alias
    effective_offset = skip if (skip is not None and offset == 0) else offset

    students, total_count = get_students(
        db=db,
        name=query_name,
        course=course,
        limit=limit,
        offset=effective_offset,
    )

    # Expose total count in response header for client pagination controls
    response.headers["X-Total-Count"] = str(total_count)
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"

    return students


@router.get(
    "/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve student by ID",
    description="Fetch a single student record by their unique ID.",
)
def get_student_endpoint(
    student_id: int,
    db: Session = Depends(get_db),
) -> StudentResponse:
    """Retrieve individual student profile."""
    student = get_student_by_id(db=db, student_id=student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} was not found.",
        )
    return student


@router.put(
    "/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Replace student details (PUT)",
    description="Full replacement of student details with validated data.",
)
def update_student_put_endpoint(
    student_id: int,
    student_in: StudentUpdatePut,
    db: Session = Depends(get_db),
) -> StudentResponse:
    """Replace editable student details with validated data."""
    try:
        return update_student_put(db=db, student_id=student_id, student_in=student_in)
    except StudentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except EmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while updating the student.",
        ) from exc


@router.patch(
    "/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update student details (PATCH)",
    description="Update only the fields supplied in the request body.",
)
def update_student_patch_endpoint(
    student_id: int,
    student_in: StudentUpdatePatch,
    db: Session = Depends(get_db),
) -> StudentResponse:
    """Update only supplied student fields."""
    try:
        return update_student_patch(db=db, student_id=student_id, student_in=student_in)
    except StudentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except EmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while partially updating the student.",
        ) from exc


@router.delete(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete student record",
    description="Permanently delete a student record by ID. Returns HTTP 204 on success.",
)
def delete_student_endpoint(
    student_id: int,
    db: Session = Depends(get_db),
) -> Response:
    """Delete a student and return HTTP 204 No Content."""
    try:
        delete_student(db=db, student_id=student_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except StudentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while deleting the student.",
        ) from exc
