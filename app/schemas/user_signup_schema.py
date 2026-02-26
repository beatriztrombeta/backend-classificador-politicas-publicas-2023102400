from pydantic import BaseModel, EmailStr, Field

class UserSignupEmail(BaseModel):
    email: EmailStr = Field(..., description="Institutional email")

class UserSignupVerifyCode(BaseModel):
    email: EmailStr = Field(..., description="Institutional email")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")