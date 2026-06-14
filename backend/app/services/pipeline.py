import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from sqlalchemy.orm import Session

from app.models import (
    Answer,
    Exam,
    ExamStatus,
    Grade,
    GradeStatus,
    PlagiarismFlag,
    Rubric,
    Submission,
)
from app.services.grading_agent import grade_answer
from app.services.ocr_service import (
    detect_plagiarism_pairs,
    ensure_upload_dir,
    extract_text_from_pdf,
    parse_rubric,
    split_answers_by_rubric,
)


def save_upload(file_bytes: bytes, filename: str, subdir: str) -> str:
    base = ensure_upload_dir() / subdir
    base.mkdir(parents=True, exist_ok=True)
    dest = base / filename
    dest.write_bytes(file_bytes)
    return str(dest)


def process_exam(db: Session, exam_id: int) -> dict:
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam or not exam.rubric:
        raise ValueError("Exam or rubric missing")

    exam.status = ExamStatus.PROCESSING
    db.commit()

    questions = parse_rubric(exam.rubric.content)
    all_answer_rows: List[Answer] = []

    for submission in exam.submissions:
        pages = extract_text_from_pdf(submission.pdf_path)
        answer_blocks = split_answers_by_rubric(pages, questions)

        for block in answer_blocks:
            answer = Answer(
                submission_id=submission.id,
                question_id=block["question_id"],
                page_number=block["page_number"],
                transcription=block["transcription"],
            )
            db.add(answer)
            db.flush()

            q = next(q for q in questions if q["id"] == block["question_id"])
            graded = grade_answer(q, block["transcription"])
            db.add(
                Grade(
                    answer_id=answer.id,
                    ai_score=graded["ai_score"],
                    ai_max_score=graded["ai_max_score"],
                    ai_justification=graded["ai_justification"],
                    status=GradeStatus.PENDING,
                )
            )
            all_answer_rows.append(answer)

    db.commit()

    # Plagiarism detection across submissions per question
    plagiarism_count = 0
    by_question: dict = {}
    for ans in all_answer_rows:
        by_question.setdefault(ans.question_id, []).append(ans)

    for qid, answers in by_question.items():
        payload = [{"question_id": a.question_id, "transcription": a.transcription} for a in answers]
        flags = detect_plagiarism_pairs(payload)
        for flag in flags:
            a = answers[flag["answer_index_a"]]
            b = answers[flag["answer_index_b"]]
            db.add(
                PlagiarismFlag(
                    answer_id=a.id,
                    similar_answer_id=b.id,
                    similarity_score=flag["similarity_score"],
                    reason=flag["reason"],
                )
            )
            plagiarism_count += 1

    exam.status = ExamStatus.READY_FOR_REVIEW
    db.commit()

    return {
        "exam_id": exam_id,
        "submissions_processed": len(exam.submissions),
        "answers_graded": len(all_answer_rows),
        "plagiarism_flags": plagiarism_count,
    }


def create_demo_exam(db: Session, instructor_id: int) -> Exam:
    rubric = {
        "questions": [
            {
                "id": "Q1",
                "prompt": "Explain Newton's second law with an example.",
                "max_points": 10,
                "criteria": ["force equals mass times acceleration", "example with object"],
            },
            {
                "id": "Q2",
                "prompt": "Define work done in physics.",
                "max_points": 10,
                "criteria": ["work is force times displacement", "joule unit"],
            },
        ]
    }

    exam = Exam(
        title="Physics Midterm — Demo",
        description="Sample exam with pre-loaded submissions for TA review demo.",
        instructor_id=instructor_id,
        status=ExamStatus.UPLOADED,
    )
    db.add(exam)
    db.flush()

    db.add(Rubric(exam_id=exam.id, content=json.dumps(rubric)))

    demo_dir = ensure_upload_dir() / "demo"
    demo_dir.mkdir(parents=True, exist_ok=True)

    samples = [
        ("STU001", "Newton law: force equals mass times acceleration. Example: pushing a box."),
        ("STU002", "F=ma. Force equals mass times acceleration. Example: car acceleration."),
        ("STU003", "Work done is force times displacement and measured in joule."),
    ]
    for sid, text in samples:
        fname = f"{sid}.txt"
        path = demo_dir / fname
        path.write_text(text)
        db.add(
            Submission(
                exam_id=exam.id,
                student_id=sid,
                pdf_path=str(path),
                page_count=1,
            )
        )

    db.commit()
    process_exam(db, exam.id)
    return exam
