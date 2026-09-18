from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..models import Attendance, Attendee, EventSurvey, User, WorkshopSurvey
from ..security import get_active_user
from .checkin import get_activity_by_token_or_404

router = APIRouter(tags=["surveys"])


def get_attendee_by_email_or_404(email: str, db: Session) -> Attendee:
    attendee = db.query(Attendee).filter(Attendee.email == email).first()
    if attendee is None:
        raise HTTPException(
            status_code=422, detail={"errors": {"email": ["Check in to an activity before answering this survey."]}}
        )
    return attendee


@router.post("/checkin/{token}/survey", response_model=schemas.WorkshopSurveyOut, status_code=201)
def submit_workshop_survey(token: str, data: schemas.WorkshopSurveyIn, db: Session = Depends(get_db)):
    activity = get_activity_by_token_or_404(token, db)
    attendee = get_attendee_by_email_or_404(data.email, db)

    attended = (
        db.query(Attendance)
        .filter(Attendance.activity_id == activity.id, Attendance.attendee_id == attendee.id)
        .first()
    )
    if attended is None:
        raise HTTPException(
            status_code=422, detail={"errors": {"email": ["Check in to this activity before answering this survey."]}}
        )

    survey = (
        db.query(WorkshopSurvey)
        .filter(WorkshopSurvey.activity_id == activity.id, WorkshopSurvey.attendee_id == attendee.id)
        .first()
    )
    fields = data.model_dump(exclude={"email"})
    if survey is None:
        survey = WorkshopSurvey(activity_id=activity.id, attendee_id=attendee.id, **fields)
        db.add(survey)
    else:
        for field, value in fields.items():
            setattr(survey, field, value)

    db.commit()
    db.refresh(survey)
    return survey


@router.post("/event-survey", response_model=schemas.EventSurveyOut, status_code=201)
def submit_event_survey(data: schemas.EventSurveyIn, db: Session = Depends(get_db)):
    attendee = get_attendee_by_email_or_404(data.email, db)

    survey = db.query(EventSurvey).filter(EventSurvey.attendee_id == attendee.id).first()
    fields = data.model_dump(exclude={"email"})
    if survey is None:
        survey = EventSurvey(attendee_id=attendee.id, **fields)
        db.add(survey)
    else:
        for field, value in fields.items():
            setattr(survey, field, value)

    db.commit()
    db.refresh(survey)
    return survey


@router.get("/activities/{activity_id}/surveys", response_model=list[schemas.WorkshopSurveyOut])
def list_workshop_surveys(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
):
    return (
        db.query(WorkshopSurvey)
        .filter(WorkshopSurvey.activity_id == activity_id)
        .order_by(WorkshopSurvey.created_at.desc())
        .all()
    )


@router.get("/event-surveys", response_model=list[schemas.EventSurveyOut])
def list_event_surveys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
):
    return db.query(EventSurvey).order_by(EventSurvey.created_at.desc()).all()
