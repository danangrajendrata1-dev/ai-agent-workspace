import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.subscription_plans import can_access_n8n, is_admin_role
from app.services import auth_service


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
        )

    try:
        payload = decode_access_token(credentials.credentials)
        subject = payload.get("sub")
        user_id = uuid.UUID(subject)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
        )

    return auth_service.get_current_active_user(db, user_id=user_id)


def require_owner(current_user=Depends(get_current_user)):
    return current_user


def require_n8n_access(current_user=Depends(get_current_user)):
    if is_admin_role(current_user.role):
        return current_user

    if not can_access_n8n(current_user.subscription_plan):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your Free plan does not include n8n access. Upgrade to Pro or Executive to save workflows.",
        )

    return current_user
