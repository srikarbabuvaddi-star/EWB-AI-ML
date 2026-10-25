"""Pydantic schemas for data validation and serialization."""

from datetime import date, datetime
import re
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator


PHONE_REGEX = re.compile(r"^\+?[0-9\s\-().]{7,25}$")


class StudentBase(BaseModel):
    """Base student schema with shared attributes and validation."""

    name: str = Field(..., min_length=2, max_length=100, description="Full name of the student")
    date_of_birth: date = Field(..., description="Date of birth (YYYY-MM-DD)")
    email: EmailStr = Field(..., description="Unique email address")
    phone: Optional[str] = Field(None, max_length=25, description="Contact phone number")
    course: Optional[str] = Field(None, max_length=100, description="Enrolled program or course")
    address: Optional[str] = Field(None, description="Residential address")
    enrollment_date: Optional[date] = Field(None, description="Date of enrollment (YYYY-MM-DD)")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Student name cannot be empty or solely whitespace.")
        if len(trimmed) < 2:
            raise ValueError("Student name must contain at least 2 characters.")
        return trimmed

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v: date) -> date:
        today = date.today()
        if v > today:
            raise ValueError("Date of birth cannot be in the future.")
        if v.year < 1900:
            raise ValueError("Date of birth cannot be prior to the year 1900.")
        return v

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        return str(v).strip().lower()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        if not trimmed:
            return None
        if not PHONE_REGEX.match(trimmed):
            raise ValueError("Phone number must contain between 7 and 25 valid digits/symbols (+, -, (), spaces).")
        return trimmed

    @field_validator("course")
    @classmethod
    def validate_course(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        return trimmed if trimmed else None

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        return trimmed if trimmed else None

    @field_validator("enrollment_date")
    @classmethod
    def validate_enrollment_date(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v.year < 1900:
            raise ValueError("Enrollment date cannot be prior to the year 1900.")
        return v


class StudentCreate(StudentBase):
    """Schema for creating a new student record."""
    pass


class StudentUpdatePut(StudentBase):
    """Schema for full replacement of a student record (PUT). All required fields must be supplied."""
    pass


class StudentUpdatePatch(BaseModel):
    """Schema for partial update of a student record (PATCH). All fields are optional."""

    name: Optional[str] = Field(None, min_length=2, max_length=100)
    date_of_birth: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=25)
    course: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    enrollment_date: Optional[date] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Student name cannot be empty or solely whitespace.")
        if len(trimmed) < 2:
            raise ValueError("Student name must contain at least 2 characters.")
        return trimmed

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v: Optional[date]) -> Optional[date]:
        if v is None:
            return None
        today = date.today()
        if v > today:
            raise ValueError("Date of birth cannot be in the future.")
        if v.year < 1900:
            raise ValueError("Date of birth cannot be prior to the year 1900.")
        return v

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: Optional[EmailStr]) -> Optional[str]:
        if v is None:
            return None
        return str(v).strip().lower()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        if not trimmed:
            return None
        if not PHONE_REGEX.match(trimmed):
            raise ValueError("Phone number must contain between 7 and 25 valid digits/symbols (+, -, (), spaces).")
        return trimmed

    @field_validator("course")
    @classmethod
    def validate_course(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        return trimmed if trimmed else None

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        return trimmed if trimmed else None

    @field_validator("enrollment_date")
    @classmethod
    def validate_enrollment_date(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v.year < 1900:
            raise ValueError("Enrollment date cannot be prior to the year 1900.")
        return v


class StudentResponse(StudentBase):
    """Schema for returning student record details."""

    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class HealthCheckResponse(BaseModel):
    """Schema for system health check status."""

    status: str
    database: str
    timestamp: datetime


class WelcomeResponse(BaseModel):
    """Schema for root API welcome response."""

    message: str
    version: str
    docs_url: str
    dashboard_url: str
