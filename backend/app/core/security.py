from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedError

_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(student_id: int, token_version: int = 0) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(student_id), "ver": token_version, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=_ALGORITHM)


def read_student_token(token: str) -> tuple[int, int]:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Your session has expired. Sign in again.") from None
    except jwt.InvalidTokenError:
        raise UnauthorizedError("Invalid authentication token.") from None

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.isdigit():
        raise UnauthorizedError("Invalid authentication token.")
    version = payload.get("ver", 0)
    if not isinstance(version, int) or version < 0:
        raise UnauthorizedError("Invalid authentication token.")
    return int(subject), version
