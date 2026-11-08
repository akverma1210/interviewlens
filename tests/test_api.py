ANSWER = """During a FastAPI project, I was responsible for a slow API endpoint. I measured the database
query time, added an index, and wrote unit and integration tests for the change. I also checked error logs
and communicated the cache trade-off. The result reduced latency by 35 percent and I learned to profile first."""


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "gemini_configured": False}


def test_create_session_builds_ordered_questions(client, session_id):
    response = client.get(f"/api/sessions/{session_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "Backend Developer"
    assert len(body["questions"]) == 5
    assert [q["position"] for q in body["questions"]] == list(range(5))
    assert body["questions"][0]["category"] == "technical"
    assert "fastapi" in body["questions"][0]["text"].lower()


def test_answer_is_scored_and_saved(client, session_id):
    session = client.get(f"/api/sessions/{session_id}").json()
    question_id = session["questions"][0]["id"]
    response = client.post(f"/api/questions/{question_id}/answer", json={"response_text": ANSWER})
    assert response.status_code == 200
    answer = response.json()
    assert answer["analysis_mode"] == "local"
    assert 0 <= answer["overall_score"] <= 100
    assert set(answer["scores"]) == {"relevance", "structure", "communication", "technical_depth"}
    assert answer["strengths"]

    duplicate = client.post(f"/api/questions/{question_id}/answer", json={"response_text": ANSWER})
    assert duplicate.status_code == 409
    saved = client.get(f"/api/sessions/{session_id}").json()
    assert saved["questions"][0]["answer"]["id"] == answer["id"]


def test_dashboard_aggregates_progress(client, session_id):
    session = client.get(f"/api/sessions/{session_id}").json()
    for question in session["questions"][:2]:
        response = client.post(f"/api/questions/{question['id']}/answer", json={"response_text": ANSWER})
        assert response.status_code == 200
    dashboard = client.get("/api/dashboard").json()
    assert dashboard["session_count"] == 1
    assert dashboard["answer_count"] == 2
    assert dashboard["average_score"] is not None
    assert dashboard["recent_sessions"][0]["answered_count"] == 2
    assert dashboard["recent_sessions"][0]["status"] == "in_progress"


def test_session_completes_after_final_answer(client, session_id):
    session = client.get(f"/api/sessions/{session_id}").json()
    for question in session["questions"]:
        client.post(f"/api/questions/{question['id']}/answer", json={"response_text": ANSWER})
    assert client.get(f"/api/sessions/{session_id}").json()["status"] == "completed"


def test_short_answer_is_rejected(client, session_id):
    question_id = client.get(f"/api/sessions/{session_id}").json()["questions"][0]["id"]
    response = client.post(f"/api/questions/{question_id}/answer", json={"response_text": "Too short"})
    assert response.status_code == 422


def test_full_length_single_style_sessions(client):
    for interview_type in ("technical", "behavioral"):
        response = client.post("/api/sessions", json={
            "role": "Software Engineer", "interview_type": interview_type, "question_count": 8
        })
        assert response.status_code == 201
        body = response.json()
        assert len(body["questions"]) == 8
        assert {question["category"] for question in body["questions"]} == {interview_type}
        assert len({question["text"] for question in body["questions"]}) == 8
