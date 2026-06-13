import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class BootstrapOwnerRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)
    display_name: str = Field(min_length=1, max_length=120)


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
    role: str
    is_active: bool
