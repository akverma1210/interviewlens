import json
import os
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import Base, engine, get_db
from app.models import Answer, InterviewSession, Question
from app.question_bank import generate_questions
from app.schemas import AnswerCreate, AnswerOut, DashboardOut, SessionCreate, SessionOut
from app.services.analyzer import analyze_locally
from app.services.gemini import analyze_with_gemini

Base.metadata.create_all(bind=engine)
app = FastAPI(title="InterviewLens API", version="1.0.0")
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def load_session(db: Session, session_id: str) -> InterviewSession:
    session = db.scalar(
        select(InterviewSession)
        .options(selectinload(InterviewSession.questions).selectinload(Question.answer))
        .where(InterviewSession.id == session_id)
    )
    if not session:
        raise HTTPException(status_code=404, detail="Practice session not found")
    return session


def answer_dict(answer: Answer) -> dict:
    feedback = json.loads(answer.feedback_json)
    return {
        "id": answer.id,
        "question_id": answer.question_id,
        "response_text": answer.response_text,
        "overall_score": answer.overall_score,
        "scores": json.loads(answer.scores_json),
        "strengths": feedback["strengths"],
        "improvements": feedback["improvements"],
        "summary": feedback["summary"],
        "analysis_mode": answer.analysis_mode,
        "created_at": answer.created_at,
    }


def session_dict(session: InterviewSession) -> dict:
    return {
        "id": session.id,
        "role": session.role,
        "level": session.level,
        "interview_type": session.interview_type,
        "job_description": session.job_description,
        "status": session.status,
        "created_at": session.created_at,
        "questions": [
            {
                "id": question.id,
                "position": question.position,
                "text": question.text,
                "category": question.category,
                "focus": json.loads(question.focus_json),
                "answer": answer_dict(question.answer) if question.answer else None,
            }
            for question in session.questions
        ],
    }


def session_summary(session: InterviewSession) -> dict:
    answers = [question.answer for question in session.questions if question.answer]
    return {
        "id": session.id,
        "role": session.role,
        "level": session.level,
        "status": session.status,
        "created_at": session.created_at,
        "question_count": len(session.questions),
        "answered_count": len(answers),
        "average_score": round(sum(a.overall_score for a in answers) / len(answers)) if answers else None,
    }


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "gemini_configured": bool(os.getenv("GEMINI_API_KEY", "").strip())}


@app.post("/api/sessions", response_model=SessionOut, status_code=201)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)):
    session = InterviewSession(
        role=payload.role,
        level=payload.level,
        interview_type=payload.interview_type,
        job_description=payload.job_description.strip(),
    )
    prompts = generate_questions(
        payload.role, payload.interview_type, payload.question_count, payload.job_description
    )
    session.questions = [
        Question(
            position=item["position"],
            text=item["text"],
            category=item["category"],
            focus_json=json.dumps(item["focus"]),
        )
        for item in prompts
    ]
    db.add(session)
    db.commit()
    return session_dict(load_session(db, session.id))


@app.get("/api/sessions/{session_id}", response_model=SessionOut)
def get_session(session_id: str, db: Session = Depends(get_db)):
    return session_dict(load_session(db, session_id))


@app.post("/api/questions/{question_id}/answer", response_model=AnswerOut)
def create_answer(question_id: str, payload: AnswerCreate, db: Session = Depends(get_db)):
    question = db.scalar(
        select(Question).options(selectinload(Question.session), selectinload(Question.answer)).where(Question.id == question_id)
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if question.answer:
        raise HTTPException(status_code=409, detail="This question already has an answer")

    focus = json.loads(question.focus_json)
    analysis = analyze_with_gemini(payload.response_text, question.text, question.session.role)
    mode = "gemini" if analysis else "local"
    if not analysis:
        analysis = analyze_locally(payload.response_text, question.text, question.session.role, focus).as_dict()

    answer = Answer(
        question_id=question.id,
        response_text=payload.response_text,
        overall_score=analysis["overall_score"],
        scores_json=json.dumps(analysis["scores"]),
        feedback_json=json.dumps({
            "strengths": analysis["strengths"],
            "improvements": analysis["improvements"],
            "summary": analysis["summary"],
        }),
        analysis_mode=mode,
    )
    db.add(answer)
    question.answer = answer
    session = load_session(db, question.session.id)
    if all(item.answer or item.id == question.id for item in session.questions):
        session.status = "completed"
    db.commit()
    db.refresh(answer)
    return answer_dict(answer)


@app.get("/api/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db)):
    sessions = list(db.scalars(
        select(InterviewSession)
        .options(selectinload(InterviewSession.questions).selectinload(Question.answer))
        .order_by(InterviewSession.created_at.desc())
    ).unique())
    answers = [question.answer for session in sessions for question in session.questions if question.answer]
    keys = ["relevance", "structure", "communication", "technical_depth"]
    skill_averages = {key: 0 for key in keys}
    if answers:
        decoded = [json.loads(answer.scores_json) for answer in answers]
        skill_averages = {
            key: round(sum(score[key] for score in decoded) / len(decoded)) for key in keys
        }
    return {
        "session_count": len(sessions),
        "answer_count": len(answers),
        "average_score": round(sum(a.overall_score for a in answers) / len(answers)) if answers else None,
        "skill_averages": skill_averages,
        "recent_sessions": [session_summary(session) for session in sessions[:5]],
    }
