from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SessionCreate(BaseModel):
    role: str = Field(min_length=2, max_length=160)
    level: Literal["Student", "Entry level", "Mid level", "Senior"] = "Entry level"
    interview_type: Literal["behavioral", "technical", "mixed"] = "mixed"
    job_description: str = Field(default="", max_length=5000)
    question_count: int = Field(default=5, ge=3, le=8)

    @field_validator("role")
    @classmethod
    def clean_role(cls, value: str) -> str:
        value = " ".join(value.split())
        if len(value) < 2:
            raise ValueError("Enter a valid role")
        return value


class AnswerCreate(BaseModel):
    response_text: str = Field(min_length=20, max_length=15000)

    @field_validator("response_text")
    @classmethod
    def clean_response(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 20:
            raise ValueError("Write at least 20 characters so there is enough to review")
        return value


class ScoreSet(BaseModel):
    relevance: int
    structure: int
    communication: int
    technical_depth: int


class AnswerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question_id: str
    response_text: str
    overall_score: int
    scores: ScoreSet
    strengths: list[str]
    improvements: list[str]
    summary: str
    analysis_mode: str
    created_at: datetime


class QuestionOut(BaseModel):
    id: str
    position: int
    text: str
    category: str
    focus: list[str]
    answer: AnswerOut | None = None


class SessionOut(BaseModel):
    id: str
    role: str
    level: str
    interview_type: str
    job_description: str
    status: str
    created_at: datetime
    questions: list[QuestionOut]


class SessionSummary(BaseModel):
    id: str
    role: str
    level: str
    status: str
    created_at: datetime
    question_count: int
    answered_count: int
    average_score: int | None


class DashboardOut(BaseModel):
    session_count: int
    answer_count: int
    average_score: int | None
    skill_averages: ScoreSet
    recent_sessions: list[SessionSummary]
