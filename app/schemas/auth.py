from pydantic import BaseModel, Field, field_validator

from app.schemas.customer import CustomerPublic, EMAIL_PATTERN, normalize_email


class LoginRequest(BaseModel):
    email: str = Field(pattern=EMAIL_PATTERN)
    password: str = Field(min_length=1)

    @field_validator("email", mode="before")
    @classmethod
    def _normalize(cls, value: object) -> object:
        return normalize_email(value) if isinstance(value, str) else value


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    customer: CustomerPublic
