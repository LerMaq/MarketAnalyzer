import hashlib
import secrets
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def generate_session_token() -> str:
    return secrets.token_urlsafe(48)

def get_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()