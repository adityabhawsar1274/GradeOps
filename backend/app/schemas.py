from datetime import datetime
from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.auth import decode_token
from app.database import get_db
from app.models import GradeStatus, User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    full_name: str


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=6)
    role: UserRole


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole

    class Config:
        from_attributes = True


class RubricQuestion(BaseModel):
    id: str
    prompt: str
    max_points: float
    criteria: List[str] = []


class RubricIn(BaseModel):
    questions: List[RubricQuestion]


class ExamCreate(BaseModel):
    title: str
    description: str = ""


class ExamOut(BaseModel):
    id: int
    title: str
    description: str
    status: str
    submission_count: int = 0

    class Config:
        from_attributes = True


class GradeOut(BaseModel):
    id: int
    ai_score: float
    ai_max_score: float
    ai_justification: str
    final_score: Optional[float]
    status: GradeStatus

    class Config:
        from_attributes = True


class PlagiarismOut(BaseModel):
    id: int
    similar_answer_id: int
    similarity_score: float
    reason: str

    class Config:
        from_attributes = True


class ReviewItemOut(BaseModel):
    grade_id: int
    exam_id: int
    exam_title: str
    student_id: str
    question_id: str
    page_number: int
    image_url: Optional[str]
    transcription: str
    grade: GradeOut
    plagiarism_flags: List[PlagiarismOut] = []


class ReviewAction(BaseModel):
    action: str  # approve | override
    final_score: Optional[float] = None
    override_reason: Optional[str] = None


class ProcessingResult(BaseModel):
    exam_id: int
    submissions_processed: int
    answers_graded: int
    plagiarism_flags: int


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_role(*roles: UserRole):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return checker
