from fastapi import Depends, HTTPException, Request
from app.database import get_db
from app.repositories.user_repository import UserRepository
from datetime import datetime, timezone


async def get_current_user(request: Request, db=Depends(get_db)):
    token = request.headers.get("Authorization")
    if token and token.startswith("Bearer "):
        token = token.split(" ")[1]
    else:
        token = request.cookies.get("session_token")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    repo = UserRepository(db)
    user = await repo.get_user_by_session_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    return user


def require_permission(perm_name: str):
    async def checker(user=Depends(get_current_user)):
        active_perms = set()
        for ur in user.user_ranks:
            if ur.expires_at is None or ur.expires_at > datetime.now(timezone.utc):
                for rp in ur.rank.rank_permissions:
                    active_perms.add(rp.permission.name)

        if perm_name not in active_perms:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user

    return checker