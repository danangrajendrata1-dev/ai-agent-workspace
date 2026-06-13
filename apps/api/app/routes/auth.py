from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.auth import (
    BootstrapOwnerRequest,
    CurrentUserResponse,
    LoginRequest,
    LoginResponse,
)
from app.services import auth_service


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/bootstrap-owner",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_201_CREATED,
)
def bootstrap_owner(payload: BootstrapOwnerRequest, db: Session = Depends(get_db)):
    user = auth_service.bootstrap_owner(
        db,
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
    )
    return user


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    access_token = auth_service.authenticate_user(
        db,
        email=payload.email,
        password=payload.password,
    )
    return LoginResponse(access_token=access_token)


@router.get("/me", response_model=CurrentUserResponse)
def get_me(current_user=Depends(get_current_user)):
    return current_user
