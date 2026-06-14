from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User, UserRole


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: int, role: UserRole) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "role": role.value, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def seed_demo_users(db: Session) -> None:
    if db.query(User).first():
        return
    db.add_all(
        [
            User(
                email="instructor@gradeops.edu",
                full_name="Dr. Sharma",
                hashed_password=hash_password("instructor123"),
                role=UserRole.INSTRUCTOR,
            ),
            User(
                email="ta@gradeops.edu",
                full_name="Priya TA",
                hashed_password=hash_password("ta123456"),
                role=UserRole.TA,
            ),
        ]
    )
    db.commit()
