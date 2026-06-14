from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Answer, User, UserRole
from app.schemas import require_role

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/{answer_id}")
def get_answer_file(
    answer_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.TA, UserRole.INSTRUCTOR)),
):
    answer = db.query(Answer).filter(Answer.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    path = answer.image_path or answer.submission.pdf_path
    if path.endswith(".txt"):
        return PlainTextResponse(open(path, "r", encoding="utf-8").read())
    return FileResponse(path)
