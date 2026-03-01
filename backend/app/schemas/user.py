from pydantic import BaseModel, EmailStr
from typing import List, Optional

class SUserRead(BaseModel):
    id: int
    email: EmailStr
    name: str

    class Config:
        from_attributes = True

class SUserFullProfile(SUserRead):
    permissions: List[str] # Плоский список прав, собранный сервисом

    class Config:
        from_attributes = True


class SUserUpdate(BaseModel):
    name: Optional[str]

    class Config:
        from_attributes = True


class SUserPasswordChange(BaseModel):
    old_password: str
    new_password: str

    class Config:
        from_attributes = True


class SSimpleMessage(BaseModel):
    detail: str

    class Config:
        from_attributes = True