from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

password = "123456"
hashed = pwd_context.hash(password)
print(hashed)