import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.subscription_plans import SubscriptionPlan, UserRole

class BootstrapOwnerRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)
    display_name: str = Field(min_length=1, max_length=120)
    model_config = ConfigDict(extra="forbid")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)
    display_name: str = Field(min_length=1, max_length=120)
    model_config = ConfigDict(extra="forbid")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=255)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    display_name: str
    role: UserRole
    subscription_plan: SubscriptionPlan
    is_active: bool

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, value):
        if value == "owner":
            return "admin"
        return value
