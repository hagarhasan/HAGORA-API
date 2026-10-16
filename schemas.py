import re

from pydantic import BaseModel, EmailStr, field_validator

from shipping import GOVERNORATE_LOOKUP
from pydantic import BaseModel, EmailStr, field_validator




def validate_password(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")

    if not re.search(r"[A-Z]", password):
        raise ValueError(
            "Password must contain at least one uppercase letter"
        )

    if not re.search(r"[a-z]", password):
        raise ValueError(
            "Password must contain at least one lowercase letter"
        )

    if not re.search(r"\d", password):
        raise ValueError(
            "Password must contain at least one number"
        )

    if not re.search(
        r"""[!@#$%^&*(),.?":{}|<>\_+=\[\]\\/'`;~-]""",
        password,
    ):
        raise ValueError(
            "Password must contain at least one special character"
        )

    return password


def normalize_email(email: str) -> str:
    # Emails are stored and compared in lowercase so that
    # Test@x.com and test@x.com are the same account.
    return str(email).strip().lower()


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, email: str):
        return normalize_email(email)

    @field_validator("password")
    @classmethod
    def validate_user_password(cls, password: str):
        return validate_password(password)


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, email: str):
        return normalize_email(email)


class BasicProfileUpdate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, email: str):
        return normalize_email(email)

    @field_validator("first_name", "last_name")
    @classmethod
    def normalize_name(cls, value: str):
        cleaned = " ".join((value or "").split())
        if not cleaned:
            raise ValueError("This field is required")
        return cleaned


class NameUpdate(BaseModel):
    first_name: str
    last_name: str

    @field_validator("first_name", "last_name")
    @classmethod
    def normalize_name(cls, value: str):
        cleaned = " ".join((value or "").split())
        if not cleaned:
            raise ValueError("This field is required")
        return cleaned


class UsernameUpdate(BaseModel):
    username: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, username: str):
        cleaned = username.strip().lower()

        if len(cleaned) < 3:
            raise ValueError("Username must be at least 3 characters long")

        if len(cleaned) > 30:
            raise ValueError("Username must be at most 30 characters long")

        if not re.fullmatch(r"[a-z0-9._-]+", cleaned):
            raise ValueError(
                "Username can only contain letters, numbers, dots, underscores, and hyphens"
            )

        return cleaned


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, email: str):
        return normalize_email(email)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_reset_password(cls, password: str):
        return validate_password(password)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, password: str):
        return validate_password(password)


class NotificationPreferencesUpdate(BaseModel):
    orderUpdates: bool
    promotions: bool
    newsletter: bool


class ProfileUpdate(BaseModel):
    username: str | None = None
    phone: str | None = None
    governorate: str | None = None
    city: str | None = None
    address: str | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, username: str | None):
        if username is None:
            return None
        return UsernameUpdate(username=username).username

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, phone: str | None):
        if phone is None:
            return None
        # Same rule as the frontend: Egyptian mobile (010 / 011 / 012 / 015)
        if not re.fullmatch(r"01[0125]\d{8}", phone):
            raise ValueError(
                "Phone number must be a valid Egyptian mobile number (11 digits starting with 01)"
            )

        return phone

    @field_validator("governorate")
    @classmethod
    def validate_governorate(cls, governorate: str | None):
        if governorate is None:
            return None
        code = (governorate or "").strip().lower()
        if code not in GOVERNORATE_LOOKUP:
            raise ValueError("Unsupported governorate code")
        return code

    @field_validator("city")
    @classmethod
    def validate_city(cls, city: str | None):
        if city is None:
            return None
        cleaned = city.strip()
        if not cleaned:
            raise ValueError("City is required")
        return cleaned

    @field_validator("address")
    @classmethod
    def validate_address(cls, address: str | None):
        if address is None:
            return None
        cleaned = address.strip()
        if len(cleaned) < 5:
            raise ValueError("Address must be at least 5 characters long")
        return cleaned


class OrderItemInput(BaseModel):
    product_id: int
    quantity: int

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, quantity: int):
        if quantity <= 0:
            raise ValueError("Quantity must be at least 1")
        return quantity


class OrderCreateRequest(BaseModel):
    idempotency_key: str | None = None
    first_name: str
    last_name: str
    phone: str
    governorate_code: str
    city: str
    address: str
    items: list[OrderItemInput]
    discount_code: str | None = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_customer_name(cls, value: str):
        cleaned = " ".join((value or "").split())
        if not cleaned:
            raise ValueError("This field is required")
        return cleaned

    @field_validator("phone")
    @classmethod
    def validate_order_phone(cls, phone: str):
        if not re.fullmatch(r"^01\d{9}$", phone):
            raise ValueError("Phone number must be a valid Egyptian mobile number")
        return phone

    @field_validator("governorate_code")
    @classmethod
    def validate_order_governorate(cls, governorate: str):
        code = (governorate or "").strip().lower()
        if code not in GOVERNORATE_LOOKUP:
            raise ValueError("Unsupported governorate code")
        return code

    @field_validator("city")
    @classmethod
    def validate_order_city(cls, city: str):
        cleaned = city.strip()
        if not cleaned:
            raise ValueError("City is required")
        return cleaned

    @field_validator("address")
    @classmethod
    def validate_order_address(cls, address: str):
        cleaned = address.strip()
        if len(cleaned) < 5:
            raise ValueError("Address must be at least 5 characters long")
        return cleaned

    @field_validator("discount_code")
    @classmethod
    def validate_discount_code(cls, value: str | None):
        if value is None:
            return None
        return value.strip().upper()

class DeleteAccountByEmailRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, email: str):
        return str(email).strip().lower()
