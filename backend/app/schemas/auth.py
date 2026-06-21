from pydantic import BaseModel, EmailStr
from typing import List

class UserLogin(BaseModel):
    username: EmailStr | str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: EmailStr | None = None
    scopes: list[str] | None = None
