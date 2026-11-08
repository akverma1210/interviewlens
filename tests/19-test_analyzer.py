from app.services.analyzer import analyze_locally


def test_local_analysis_rewards_specific_structured_answer():
    answer = """During my FastAPI project, I was responsible for reducing slow API responses.
I measured database query latency, added an index and used unit and integration tests to check the change.
Because the endpoint still had repeated reads, I added a small cache. The result reduced response time by 42%.
I communicated the trade-off to my teammate and documented the deployment and regression checks."""
    result = analyze_locally(
        answer,
        "A feature you own is slow in production. How would you investigate it?",
        "Backend Developer",
        ["measure", "database", "query", "cache", "test"],
    )
    assert result.overall_score >= 75
    assert result.scores["technical_depth"] >= 80
    assert len(result.strengths) >= 2
    assert len(result.improvements) >= 1


def test_short_answer_gets_constructive_feedback():
    result = analyze_locally("I would fix it.", "How would you debug an API?", "Developer", ["test"])
    assert result.overall_score < 60
    assert any("example" in item.lower() for item in result.improvements)
