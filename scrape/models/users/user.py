from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class UserResponse(BaseModel):
    id: UUID = Field(
        ...,
        title="ID",
        description="The ID of the user"
    )
    email: EmailStr = Field(
        ...,
        title="Email",
        description="The email of the user"
    )
    username: Optional[str] = Field(
        ...,
        title="Username",
        description="The username of the user"
    )
    is_superuser: bool = Field(
        ...,
        title="Is Superuser",
        description="Whether the user is a superuser"
    )
    is_admin: bool = Field(
        ...,
        title="Is Admin",
        description="Whether the user is an admin"
    )
    is_active: bool = Field(
        ...,
        title="Is Active",
        description="Whether the user is active"
    )
    created_at: datetime = Field(
        ...,
        title="Created At",
        description="The created at of the user"
    )
    updated_at: Optional[datetime] = Field(
        ...,
        title="Updated At",
        description="The updated at of the user"
    )


class User(BaseModel):
    email: EmailStr = Field(
        ...,
        title="Email",
        description="The email of the user"
    )
    username: Optional[str] = Field(
        ...,
        title="Username",
        description="The username of the user"
    )
    password: str = Field(
        ...,
        title="Password",
        description="The password of the user",
        examples=["Adj@kf243Wf&fj9dQ"]
    )
    is_superuser: Optional[bool] = Field(
        False,
        title="Is Superuser",
        description="Whether the user is a superuser"
    )
    is_admin: Optional[bool] = Field(
        False,
        title="Is Admin",
        description="Whether the user is an admin"
    )
    is_active: bool = Field(
        ...,
        title="Is Active",
        description="Whether the user is active"
    )


class UserInDB(UserResponse):
    hashed_password: str


class UserUpdateRequest(BaseModel):
    username: Optional[str] = Field(
        ...,
        title="Username",
        description="The username of the user"
    )
    email: Optional[EmailStr] = Field(
        ...,
        title="Email",
        description="The email of the user"
    )
    is_superuser: Optional[bool] = Field(
        False,
        title="Is Superuser",
        description="Whether the user is a superuser"
    )
    is_admin: Optional[bool] = Field(
        False,
        title="Is Admin",
        description="Whether the user is an admin"
    )
    is_active: Optional[bool] = Field(
        ...,
        title="Is Active",
        description="Whether the user is active"
    )


class UserPasswordUpdateRequest(BaseModel):
    old_password: str = Field(
        ...,
        title="Old Password",
        description="The old password of the user",
        examples=["Adj@kf243Wf&fj9dQ"]
    )
    new_password: str = Field(
        ...,
        title="New Password",
        description="The new password of the user",
        examples=["Adj#kf043Wf&fj9dQ"]
    )


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
