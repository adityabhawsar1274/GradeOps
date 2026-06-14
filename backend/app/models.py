import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class UserRole(str, enum.Enum):
    INSTRUCTOR = "instructor"
    TA = "ta"


class GradeStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    OVERRIDDEN = "overridden"


class ExamStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY_FOR_REVIEW = "ready_for_review"
    COMPLETED = "completed"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    exams = relationship("Exam", back_populates="instructor")


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(ExamStatus), default=ExamStatus.UPLOADED)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    instructor = relationship("User", back_populates="exams")
    rubric = relationship("Rubric", back_populates="exam", uselist=False)
    submissions = relationship("Submission", back_populates="exam")


class Rubric(Base):
    __tablename__ = "rubrics"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), unique=True, nullable=False)
    content = Column(Text, nullable=False)  # JSON string

    exam = relationship("Exam", back_populates="rubric")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    student_id = Column(String(64), nullable=False)
    pdf_path = Column(String(512), nullable=False)
    page_count = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    exam = relationship("Exam", back_populates="submissions")
    answers = relationship("Answer", back_populates="submission")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    question_id = Column(String(64), nullable=False)
    page_number = Column(Integer, default=1)
    image_path = Column(String(512), nullable=True)
    transcription = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    submission = relationship("Submission", back_populates="answers")
    grade = relationship("Grade", back_populates="answer", uselist=False)
    plagiarism_flags = relationship(
        "PlagiarismFlag",
        back_populates="answer",
        foreign_keys="PlagiarismFlag.answer_id",
    )


class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    answer_id = Column(Integer, ForeignKey("answers.id"), unique=True, nullable=False)
    ai_score = Column(Float, nullable=False)
    ai_max_score = Column(Float, nullable=False)
    ai_justification = Column(Text, nullable=False)
    final_score = Column(Float, nullable=True)
    status = Column(Enum(GradeStatus), default=GradeStatus.PENDING)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    override_reason = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    answer = relationship("Answer", back_populates="grade")
    reviewer = relationship("User")


class PlagiarismFlag(Base):
    __tablename__ = "plagiarism_flags"

    id = Column(Integer, primary_key=True, index=True)
    answer_id = Column(Integer, ForeignKey("answers.id"), nullable=False)
    similar_answer_id = Column(Integer, ForeignKey("answers.id"), nullable=False)
    similarity_score = Column(Float, nullable=False)
    reason = Column(Text, default="")

    answer = relationship("Answer", foreign_keys=[answer_id], back_populates="plagiarism_flags")
