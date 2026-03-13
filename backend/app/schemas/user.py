from pydantic import BaseModel, EmailStr
from typing import List, Optional


class SUserLimits(BaseModel):
    analysis: int
    chat: int


class SUserUsage(BaseModel):
    analysis: int
    chat: int


class SUserRead(BaseModel):
    id: int
    email: EmailStr
    name: str

    class Config:
        from_attributes = True


class SUserFullProfile(SUserRead):
    permissions: List[str]
    tariff: str = "free"  # "free" | "premium"
    limits: SUserLimits
    usage: SUserUsage

    class Config:
        from_attributes = True


class SSubscribeRequest(BaseModel):
    amount: int


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