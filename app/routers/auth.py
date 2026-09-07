from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..models import User
from ..security import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=schemas.TokenResponse, status_code=status.HTTP_201_CREATED)
def register(data: schemas.RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=422, detail={"errors": {"email": ["Email is already registered."]}})

    user = User(name=data.name, email=data.email, hashed_password=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return {"user": user, "token": token}


@router.post("/login", response_model=schemas.TokenResponse)
def login(data: schemas.LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=422, detail="Invalid credentials.")

    token = create_access_token(user.id)
    return {"user": user, "token": token}


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Logged out."}


@router.get("/user", response_model=schemas.UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
