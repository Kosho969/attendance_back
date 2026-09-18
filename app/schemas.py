from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    must_change_password: bool

    model_config = {"from_attributes": True}


class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str
    password_confirmation: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v

    @field_validator("password_confirmation")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Password confirmation does not match.")
        return v


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    user: UserOut
    token: str


class ChangePasswordIn(BaseModel):
    current_password: str
    password: str
    password_confirmation: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v

    @field_validator("password_confirmation")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Password confirmation does not match.")
        return v


class ActivityCreate(BaseModel):
    title: str
    subject: str
    host_id: int
    location: str | None = None
    starts_at: datetime | None = None


class ActivityUpdate(BaseModel):
    title: str | None = None
    subject: str | None = None
    host_id: int | None = None
    location: str | None = None
    starts_at: datetime | None = None


class ActivityOut(BaseModel):
    id: int
    title: str
    subject: str
    host_id: int
    location: str | None
    starts_at: datetime | None
    qr_token: str
    created_at: datetime
    updated_at: datetime
    host: UserOut
    attendances_count: int = 0

    model_config = {"from_attributes": True}


class ActivityPublic(BaseModel):
    id: int
    title: str
    subject: str
    location: str | None
    host: UserOut

    model_config = {"from_attributes": True}


class AttendeeOut(BaseModel):
    id: int
    name: str
    email: EmailStr

    model_config = {"from_attributes": True}


class AttendanceOut(BaseModel):
    id: int
    activity_id: int
    attendee_id: int
    checked_in_at: datetime
    attendee: AttendeeOut

    model_config = {"from_attributes": True}


class CheckinIn(BaseModel):
    name: str
    email: EmailStr


class CheckinResult(BaseModel):
    attendee: AttendeeOut
    checked_in_at: datetime
    already_checked_in: bool
    event_survey_completed: bool


class DesiredLevel(str, Enum):
    bajo = "bajo"
    intermedio = "intermedio"
    alto = "alto"


class MostEnjoyed(str, Enum):
    experiencia = "experiencia"
    convivencia = "convivencia"
    aprendizaje = "aprendizaje"


class WorkshopSurveyIn(BaseModel):
    email: EmailStr
    enjoyment: int = Field(ge=1, le=5)
    learning: int = Field(ge=1, le=5)
    applicability: int = Field(ge=1, le=5)
    second_part_wanted: bool
    instructor_competence: int = Field(ge=1, le=5)
    workshop_suggestion: str | None = None
    instructor_suggestion: str | None = None


class WorkshopSurveyOut(BaseModel):
    id: int
    activity_id: int
    enjoyment: int
    learning: int
    applicability: int
    second_part_wanted: bool
    instructor_competence: int
    workshop_suggestion: str | None
    instructor_suggestion: str | None
    created_at: datetime
    attendee: AttendeeOut

    model_config = {"from_attributes": True}


class EventSurveyIn(BaseModel):
    email: EmailStr
    overall_rating: int = Field(ge=1, le=5)
    workshops_informative: int = Field(ge=1, le=5)
    desired_level: DesiredLevel
    would_participate_again: bool
    interested_in_hosting: bool
    most_enjoyed: MostEnjoyed


class EventSurveyOut(BaseModel):
    id: int
    overall_rating: int
    workshops_informative: int
    desired_level: DesiredLevel
    would_participate_again: bool
    interested_in_hosting: bool
    most_enjoyed: MostEnjoyed
    created_at: datetime
    attendee: AttendeeOut

    model_config = {"from_attributes": True}
