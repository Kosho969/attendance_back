from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr

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
