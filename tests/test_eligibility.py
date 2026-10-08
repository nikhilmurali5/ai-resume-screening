import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.eligibility import check_eligibility
from src.models import ResumeData


def make_resume(text: str) -> ResumeData:
    return ResumeData(
        filename="test.pdf",
        raw_text=text,
        candidate_name="Test Candidate",
        skills=[],
    )


def test_python_and_ai_candidate_is_eligible():
    resume = make_resume(
        "Python FastAPI developer. Built a RAG application "
        "using LangChain and vector search."
    )

    result = check_eligibility(resume)

    assert result.eligible is True
    assert result.python_evidence
    assert result.ai_evidence


def test_python_without_ai_is_rejected():
    resume = make_resume(
        "Python FastAPI backend developer with PostgreSQL and REST APIs."
    )

    result = check_eligibility(resume)

    assert result.eligible is False
    assert "No evidence of AI/LLM/RAG/agentic work" in result.rejection_reasons


def test_ai_without_python_is_rejected():
    resume = make_resume(
        "Built an LLM RAG application using LangChain and embeddings."
    )

    result = check_eligibility(resume)

    assert result.eligible is False
    assert "No evidence of Python stack" in result.rejection_reasons


def test_java_react_only_candidate_is_rejected():
    resume = make_resume(
        "Java developer with React, JavaScript and Spring Boot experience."
    )

    result = check_eligibility(resume)

    assert result.eligible is False
    assert len(result.rejection_reasons) == 2