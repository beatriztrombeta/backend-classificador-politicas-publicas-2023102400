from pydantic import BaseModel, EmailStr

class UserLogin(BaseModel):
    email: EmailStr

class VerifyCode(BaseModel):
    email: EmailStr
    code: str