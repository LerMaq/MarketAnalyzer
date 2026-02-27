from pydantic import BaseModel, EmailStr

class SUserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str

class SUserLogin(BaseModel):
    email: EmailStr
    password: str

class SAuthResponse(BaseModel):
    session_token: str
    message: str

    class Config:
        from_attributes = True