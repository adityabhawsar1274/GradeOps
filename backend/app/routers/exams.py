import json
import uuid
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Exam, ExamStatus, Rubric, Submission, User, UserRole
from app.schemas import ExamCreate, ExamOut, ProcessingResult, require_role
from app.services.pipeline import create_demo_exam, process_exam, save_upload

router = APIRouter(prefix="/exams", tags=["exams"])


@router.get("", response_model=List[ExamOut])
def list_exams(db: Session = Depends(get_db), user: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.TA))):
    exams = db.query(Exam).order_by(Exam.created_at.desc()).all()
    return [
        ExamOut(
            id=e.id,
            title=e.title,
            description=e.description,
            status=e.status.value,
            submission_count=len(e.submissions),
        )
        for e in exams
    ]


@router.post("", response_model=ExamOut)
def create_exam(
    payload: ExamCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.INSTRUCTOR)),
):
    exam = Exam(title=payload.title, description=payload.description, instructor_id=user.id)
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return ExamOut(
        id=exam.id,
        title=exam.title,
        description=exam.description,
        status=exam.status.value,
        submission_count=0,
    )


@router.post("/demo")
def seed_demo(db: Session = Depends(get_db), user: User = Depends(require_role(UserRole.INSTRUCTOR))):
    exam = create_demo_exam(db, user.id)
    return {"exam_id": exam.id, "title": exam.title, "status": exam.status.value}


@router.post("/{exam_id}/rubric")
def upload_rubric(
    exam_id: int,
    rubric: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.INSTRUCTOR)),
):
    exam = db.query(Exam).filter(Exam.id == exam_id, Exam.instructor_id == user.id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    content = rubric.file.read().decode("utf-8")
    json.loads(content)  # validate JSON
    if exam.rubric:
        exam.rubric.content = content
    else:
        db.add(Rubric(exam_id=exam.id, content=content))
    db.commit()
    return {"status": "rubric_saved"}


@router.post("/{exam_id}/submissions")
async def upload_submissions(
    exam_id: int,
    files: List[UploadFile] = File(...),
    student_ids: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.INSTRUCTOR)),
):
    exam = db.query(Exam).filter(Exam.id == exam_id, Exam.instructor_id == user.id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    ids = [s.strip() for s in student_ids.split(",") if s.strip()]
    count = 0
    for i, f in enumerate(files):
        sid = ids[i] if i < len(ids) else f"STU{uuid.uuid4().hex[:6].upper()}"
        data = await f.read()
        path = save_upload(data, f"{sid}_{f.filename}", f"exam_{exam_id}")
        db.add(Submission(exam_id=exam.id, student_id=sid, pdf_path=path))
        count += 1
    db.commit()
    return {"uploaded": count}


def _run_pipeline(exam_id: int):
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        process_exam(db, exam_id)
    finally:
        db.close()


@router.post("/{exam_id}/process", response_model=ProcessingResult)
def trigger_process(
    exam_id: int,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.INSTRUCTOR)),
):
    exam = db.query(Exam).filter(Exam.id == exam_id, Exam.instructor_id == user.id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    if not exam.rubric:
        raise HTTPException(status_code=400, detail="Upload rubric first")
    if not exam.submissions:
        raise HTTPException(status_code=400, detail="Upload submissions first")

    background.add_task(_run_pipeline, exam_id)
    exam.status = ExamStatus.PROCESSING
    db.commit()
    return ProcessingResult(exam_id=exam_id, submissions_processed=0, answers_graded=0, plagiarism_flags=0)


@router.post("/{exam_id}/process-sync", response_model=ProcessingResult)
def process_sync(
    exam_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.INSTRUCTOR)),
):
    exam = db.query(Exam).filter(Exam.id == exam_id, Exam.instructor_id == user.id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    result = process_exam(db, exam_id)
    return ProcessingResult(**result)
