"""Pydantic validation layer (PRD §7.3). Pure validation, no I/O."""
from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

import config


class Role(str, Enum):
    student = "student"
    admin = "admin"


class Condition(str, Enum):
    new = "new"
    used = "used"


class ProductStatus(str, Enum):
    available = "available"
    sold = "sold"


class OrderStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"


class UserCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=config.PASSWORD_MIN_LENGTH)
    phone: Optional[str] = Field(default=None, max_length=20)

    @field_validator("email")
    @classmethod
    def institutional_domain(cls, v: str) -> str:
        v = v.lower()
        if not v.endswith("@" + config.INSTITUTION_DOMAIN):
            raise ValueError(
                f"must be a Caleb University email (@{config.INSTITUTION_DOMAIN})"
            )
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < config.PASSWORD_MIN_LENGTH:
            raise ValueError(
                f"password must be at least {config.PASSWORD_MIN_LENGTH} characters"
            )
        classes = [
            any(c.islower() for c in v),
            any(c.isupper() for c in v),
            any(c.isdigit() for c in v),
            any(not c.isalnum() for c in v),
        ]
        if sum(classes) < 3:
            raise ValueError(
                "password must mix at least three of: lowercase, uppercase, "
                "digits, symbols"
            )
        return v

    @field_validator("phone")
    @classmethod
    def phone_shape(cls, v: Optional[str]) -> str | None:
        if v in (None, ""):
            return None
        cleaned = v.strip()
        digits = cleaned.lstrip("+")
        if not digits.isdigit() or not (7 <= len(digits) <= 20):
            raise ValueError("phone must be 7–20 digits, optionally prefixed with +")
        return cleaned


class ProfileUpdate(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)

    _phone_shape = field_validator("phone")(UserCreate.phone_shape.__func__)  # type: ignore[attr-defined]


class ProductCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: Optional[str] = None
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    condition: Condition
    quantity: int = Field(default=1, ge=1)
    category_id: int

    @field_validator("description")
    @classmethod
    def trim_description(cls, v: Optional[str]) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    description: Optional[str] = Field(default=None, max_length=255)


class OrderItemIn(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)
