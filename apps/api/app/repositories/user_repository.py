from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.subscription_plans import (
    DEFAULT_REGISTER_SUBSCRIPTION_PLAN,
    ROLE_ADMIN,
    ROLE_USER,
)
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


def create_user(
    db: Session,
    *,
    email: str,
    password_hash: str,
    display_name: str,
    role: str = ROLE_USER,
    subscription_plan: str = DEFAULT_REGISTER_SUBSCRIPTION_PLAN,
) -> User:
    user = User(
        email=email,
        password_hash=password_hash,
        display_name=display_name,
        role=role,
        subscription_plan=subscription_plan,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def create_admin_user(
    db: Session,
    *,
    email: str,
    password_hash: str,
    display_name: str,
) -> User:
    return create_user(
        db,
        email=email,
        password_hash=password_hash,
        display_name=display_name,
        role=ROLE_ADMIN,
    )


def create_owner_user(
    db: Session,
    *,
    email: str,
    password_hash: str,
    display_name: str,
) -> User:
    return create_admin_user(
        db,
        email=email,
        password_hash=password_hash,
        display_name=display_name,
    )
