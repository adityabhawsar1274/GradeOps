from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Answer, Exam, Grade, GradeStatus, PlagiarismFlag, Submission, User, UserRole
from app.schemas import GradeOut, PlagiarismOut, ReviewAction, ReviewItemOut, require_role

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/queue", response_model=List[ReviewItemOut])
def review_queue(
    status: Optional[GradeStatus] = Query(GradeStatus.PENDING),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.TA, UserRole.INSTRUCTOR)),
):
    query = (
        db.query(Grade)
        .join(Answer)
        .join(Submission)
        .join(Exam)
        .options(
            joinedload(Grade.answer).joinedload(Answer.submission).joinedload(Submission.exam),
            joinedload(Grade.answer).joinedload(Answer.plagiarism_flags),
        )
        .filter(Grade.status == status)
        .order_by(Grade.created_at.asc())
        .limit(limit)
    )
    items = []
    for g in query:
        ans = g.answer
        sub = ans.submission
        exam = sub.exam
        items.append(
            ReviewItemOut(
                grade_id=g.id,
                exam_id=exam.id,
                exam_title=exam.title,
                student_id=sub.student_id,
                question_id=ans.question_id,
                page_number=ans.page_number,
                image_url=f"/api/files/{ans.id}" if ans.image_path else None,
                transcription=ans.transcription,
                grade=GradeOut.model_validate(g),
                plagiarism_flags=[PlagiarismOut.model_validate(f) for f in ans.plagiarism_flags],
            )
        )
    return items


@router.post("/{grade_id}/action")
def review_action(
    grade_id: int,
    payload: ReviewAction,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.TA, UserRole.INSTRUCTOR)),
):
    grade = db.query(Grade).filter(Grade.id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")

    action = payload.action.lower()
    if action == "approve":
        grade.status = GradeStatus.APPROVED
        grade.final_score = grade.ai_score
    elif action == "override":
        if payload.final_score is None:
            raise HTTPException(status_code=400, detail="final_score required for override")
        grade.status = GradeStatus.OVERRIDDEN
        grade.final_score = payload.final_score
        grade.override_reason = payload.override_reason or ""
    else:
        raise HTTPException(status_code=400, detail="action must be approve or override")

    grade.reviewer_id = user.id
    grade.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": grade.status.value, "final_score": grade.final_score}


@router.get("/stats")
def review_stats(
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.TA, UserRole.INSTRUCTOR)),
):
    total = db.query(Grade).count()
    pending = db.query(Grade).filter(Grade.status == GradeStatus.PENDING).count()
    approved = db.query(Grade).filter(Grade.status == GradeStatus.APPROVED).count()
    overridden = db.query(Grade).filter(Grade.status == GradeStatus.OVERRIDDEN).count()
    flags = db.query(PlagiarismFlag).count()
    return {
        "total_grades": total,
        "pending": pending,
        "approved": approved,
        "overridden": overridden,
        "plagiarism_flags": flags,
    }
