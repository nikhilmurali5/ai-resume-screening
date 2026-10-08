import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models import ResumeData
from src.scorer import calculate_score


def make_resume(text: str) -> ResumeData:
    return ResumeData(
        filename="test.pdf",
        raw_text=text,
        candidate_name="Test Candidate",
        skills=[],
    )


def test_strong_backend_ai_resume_scores_high():
    resume = make_resume(
        """
        Python FastAPI backend developer.
        Built a multi-agent RAG system using LangGraph and LangChain.
        Used PostgreSQL, Redis, Docker and AWS.
        Added pytest testing and caching.
        """
    )

    score = calculate_score(resume)

    assert score.ai_project_depth >= 25
    assert score.python_backend >= 20
    assert score.cloud_fullstack >= 5
    assert score.engineering_depth >= 1
    assert score.total >= 60


def test_python_backend_without_ai_gets_lower_ai_score():
    resume = make_resume(
        """
        Python developer using FastAPI and PostgreSQL.
        Built REST APIs and backend services.
        """
    )

    score = calculate_score(resume)

    assert score.python_backend > 0
    assert score.ai_project_depth == 0


def test_empty_resume_scores_zero():
    resume = make_resume("Java developer with basic web development experience.")

    score = calculate_score(resume)

    assert score.ai_project_depth == 0
    assert score.python_backend == 0
    assert score.cloud_fullstack == 0
    assert score.github == 0
    assert score.engineering_depth == 0
    assert score.total == 0