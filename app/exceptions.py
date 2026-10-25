"""Custom domain exceptions for students database application."""


class StudentException(Exception):
    """Base exception for student application."""
    pass


class StudentNotFoundError(StudentException):
    """Raised when a requested student is not found."""

    def __init__(self, student_id: int):
        self.student_id = student_id
        super().__init__(f"Student with ID {student_id} was not found.")


class EmailAlreadyExistsError(StudentException):
    """Raised when attempting to create or update a student with a duplicate email."""

    def __init__(self, email: str):
        self.email = email
        super().__init__(f"A student with email '{email}' already exists.")


class DatabaseOperationError(StudentException):
    """Raised when an unexpected database transaction failure occurs."""

    def __init__(self, message: str = "A database error occurred while processing your request."):
        super().__init__(message)
