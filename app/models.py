import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def new_id() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    role: Mapped[str] = mapped_column(String(160), nullable=False)
    level: Mapped[str] = mapped_column(String(60), nullable=False)
    interview_type: Mapped[str] = mapped_column(String(30), nullable=False)
    job_description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="in_progress")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    questions: Mapped[list["Question"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="Question.position"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("interview_sessions.id"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    focus_json: Mapped[str] = mapped_column(Text, default="[]")

    session: Mapped[InterviewSession] = relationship(back_populates="questions")
    answer: Mapped["Answer | None"] = relationship(
        back_populates="question", cascade="all, delete-orphan", uselist=False
    )


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), unique=True, nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    scores_json: Mapped[str] = mapped_column(Text, nullable=False)
    feedback_json: Mapped[str] = mapped_column(Text, nullable=False)
    analysis_mode: Mapped[str] = mapped_column(String(20), default="local")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    question: Mapped[Question] = relationship(back_populates="answer")
