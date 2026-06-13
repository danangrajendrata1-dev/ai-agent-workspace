from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User


def get_by_email(db: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return db.execute(statement).scalar_one_or_none()


def get_by_id(db: Session, user_id) -> User | None:
    statement = select(User).where(User.id == user_id)
    return db.execute(statement).scalar_one_or_none()


def count_active_users(db: Session) -> int:
    statement = select(func.count(User.id)).where(
        User.is_active.is_(True),
        User.deleted_at.is_(None),
    )
    return db.execute(statement).scalar_one()


def create_owner_user(
    db: Session,
    *,
    email: str,
    password_hash: str,
    display_name: str,
) -> User:
    user = User(
        email=email,
        password_hash=password_hash,
        display_name=display_name,
        role="owner",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
