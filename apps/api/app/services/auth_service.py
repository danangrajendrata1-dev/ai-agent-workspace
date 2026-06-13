from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.repositories import user_repository
from app.services import log_service


def normalize_email(email: str) -> str:
    return email.strip().lower()


def bootstrap_owner(db: Session, *, email: str, password: str, display_name: str):
    if user_repository.count_active_users(db) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner bootstrap is no longer available.",
        )

    normalized_email = normalize_email(email)
    existing_user = user_repository.get_by_email(db, normalized_email)
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner bootstrap is no longer available.",
        )

    user = user_repository.create_owner_user(
        db,
        email=normalized_email,
        password_hash=hash_password(password),
        display_name=display_name.strip(),
    )
    log_service.record_activity(
        db,
        actor_type="user",
        actor_id=user.id,
        request_id=None,
        event_type="auth.bootstrap_owner",
        message="Owner account bootstrapped.",
        metadata_json={"email": normalized_email},
    )
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, *, email: str, password: str) -> str:
    normalized_email = normalize_email(email)
    user = user_repository.get_by_email(db, normalized_email)

    if (
        user is None
        or not user.is_active
        or user.deleted_at is not None
        or not verify_password(password, user.password_hash)
        ):
        log_service.record_activity(
            db,
            actor_type="system",
            actor_id=None,
            request_id=None,
            event_type="auth.login_failed",
            message="Authentication failed.",
            metadata_json={"email": normalized_email},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    log_service.record_activity(
        db,
        actor_type="user",
        actor_id=user.id,
        request_id=None,
        event_type="auth.login_success",
        message="Authentication succeeded.",
        metadata_json={"email": normalized_email},
    )
    db.commit()
    return create_access_token(subject=str(user.id))


def get_current_active_user(db: Session, *, user_id):
    user = user_repository.get_by_id(db, user_id)
    if user is None or not user.is_active or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
        )
    return user
