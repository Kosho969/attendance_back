from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..models import Activity, User
from ..security import get_active_user

router = APIRouter(tags=["activities"])


def get_activity_or_404(activity_id: int, db: Session) -> Activity:
    activity = db.get(Activity, activity_id)
    if activity is None:
        raise HTTPException(status_code=404, detail="Activity not found.")
    return activity


@router.get("/activities", response_model=list[schemas.ActivityOut])
def list_activities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
):
    return db.query(Activity).order_by(Activity.created_at.desc()).all()


@router.post("/activities", response_model=schemas.ActivityOut, status_code=status.HTTP_201_CREATED)
def create_activity(
    data: schemas.ActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
):
    if db.get(User, data.host_id) is None:
        raise HTTPException(status_code=422, detail={"errors": {"host_id": ["Selected host does not exist."]}})

    activity = Activity(
        title=data.title,
        subject=data.subject,
        host_id=data.host_id,
        location=data.location,
        starts_at=data.starts_at,
        created_by=current_user.id,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


@router.get("/activities/{activity_id}", response_model=schemas.ActivityOut)
def get_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
):
    return get_activity_or_404(activity_id, db)


@router.put("/activities/{activity_id}", response_model=schemas.ActivityOut)
def update_activity(
    activity_id: int,
    data: schemas.ActivityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
):
    activity = get_activity_or_404(activity_id, db)

    if data.host_id is not None and db.get(User, data.host_id) is None:
        raise HTTPException(status_code=422, detail={"errors": {"host_id": ["Selected host does not exist."]}})

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(activity, field, value)

    db.commit()
    db.refresh(activity)
    return activity


@router.delete("/activities/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
):
    activity = get_activity_or_404(activity_id, db)
    db.delete(activity)
    db.commit()


@router.get("/activities/{activity_id}/attendances", response_model=list[schemas.AttendanceOut])
def list_attendances(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
):
    activity = get_activity_or_404(activity_id, db)
    return sorted(activity.attendances, key=lambda a: a.checked_in_at, reverse=True)
