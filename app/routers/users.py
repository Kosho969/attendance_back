from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..models import User
from ..security import get_active_user

router = APIRouter(tags=["users"])


@router.get("/users", response_model=list[schemas.UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
):
    return db.query(User).order_by(User.name).all()
