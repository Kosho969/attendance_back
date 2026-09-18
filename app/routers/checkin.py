from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..models import Activity, Attendance, Attendee

router = APIRouter(tags=["checkin"])


def get_activity_by_token_or_404(token: str, db: Session) -> Activity:
    activity = db.query(Activity).filter(Activity.qr_token == token).first()
    if activity is None:
        raise HTTPException(status_code=404, detail="Activity not found.")
    return activity


@router.get("/checkin/{token}", response_model=schemas.ActivityPublic)
def show_activity(token: str, db: Session = Depends(get_db)):
    return get_activity_by_token_or_404(token, db)


@router.post("/checkin/{token}", response_model=schemas.CheckinResult)
def submit_checkin(token: str, data: schemas.CheckinIn, db: Session = Depends(get_db)):
    activity = get_activity_by_token_or_404(token, db)

    attendee = db.query(Attendee).filter(Attendee.email == data.email).first()
    if attendee is None:
        attendee = Attendee(name=data.name, email=data.email)
        db.add(attendee)
        db.commit()
        db.refresh(attendee)

    attendance = (
        db.query(Attendance)
        .filter(Attendance.activity_id == activity.id, Attendance.attendee_id == attendee.id)
        .first()
    )
    already_checked_in = attendance is not None
    if attendance is None:
        attendance = Attendance(activity_id=activity.id, attendee_id=attendee.id)
        db.add(attendance)
        db.commit()
        db.refresh(attendance)

    return {
        "attendee": attendee,
        "checked_in_at": attendance.checked_in_at,
        "already_checked_in": already_checked_in,
        "event_survey_completed": attendee.event_survey is not None,
    }
