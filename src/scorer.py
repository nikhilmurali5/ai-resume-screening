from src.llm import LLMAnalysis
from dataclasses import dataclass, field
from typing import List

from .models import ResumeData


@dataclass
class ScoreBreakdown:
    ai_project_depth: int = 0
    python_backend: int = 0
    cloud_fullstack: int = 0
    github: int = 0
    engineering_depth: int = 0

    reasons: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return (
            self.ai_project_depth
            + self.python_backend
            + self.cloud_fullstack
            + self.github
            + self.engineering_depth
        )


def _contains(text: str, signal: str) -> bool:
    return signal.lower() in text.lower()


def score_ai_project_depth(
    resume: ResumeData,
    breakdown: ScoreBreakdown,
) -> None:
    """
    Maximum: 40 points.

    Rewards meaningful AI systems rather than simply mentioning
    an AI framework.
    """

    text = resume.raw_text.lower()

    score = 0

    strong_signals = {
        "multi-agent": 10,
        "multi agent": 10,
        "langgraph": 8,
        "agentic": 8,
        "tool calling": 7,
        "tool-calling": 7,
        "rag": 7,
        "retrieval": 5,
        "vector search": 5,
        "embeddings": 4,
        "evaluation": 4,
        "llm": 3,
        "langchain": 4,
        "llamaindex": 4,
    }

    matched = []

    for signal, points in strong_signals.items():
        if signal in text:
            score += points
            matched.append(signal)

    score = min(score, 40)

    # Penalize extremely shallow AI projects.
    shallow_signals = [
        "chatbot using api",
        "simple chatbot",
        "basic chatbot",
        "llm api wrapper",
    ]

    if any(signal in text for signal in shallow_signals):
        score = max(0, score - 8)
        breakdown.concerns.append(
            "Possible shallow LLM/API-wrapper project"
        )

    breakdown.ai_project_depth = score

    if matched:
        breakdown.reasons.append(
            "AI evidence: " + ", ".join(matched[:8])
        )

    if score >= 30:
        breakdown.strengths.append(
            "Strong AI/agentic project depth"
        )


def score_python_backend(
    resume: ResumeData,
    breakdown: ScoreBreakdown,
) -> None:
    """
    Maximum: 30 points.

    Gives more weight to backend implementation signals.
    """

    text = resume.raw_text.lower()

    score = 0

    signals = {
        "python": 5,
        "fastapi": 6,
        "flask": 4,
        "django": 4,
        "async": 3,
        "asynchronous": 3,
        "postgresql": 3,
        "redis": 3,
        "rest api": 2,
        "backend": 2,
        "api": 1,
        "sql": 1,
    }

    matched = []

    for signal, points in signals.items():
        if signal in text:
            score += points
            matched.append(signal)

    score = min(score, 30)

    breakdown.python_backend = score

    if matched:
        breakdown.reasons.append(
            "Backend evidence: " + ", ".join(matched[:8])
        )

    if score >= 20:
        breakdown.strengths.append(
            "Strong Python/backend engineering"
        )

    if "python" in text and score < 10:
        breakdown.concerns.append(
            "Python appears but backend implementation evidence is limited"
        )


def score_cloud_fullstack(
    resume: ResumeData,
    breakdown: ScoreBreakdown,
) -> None:
    """
    Maximum: 15 points.
    """

    text = resume.raw_text.lower()

    score = 0
    matched = []

    signals = {
        "docker": 4,
        "gcp": 4,
        "google cloud": 4,
        "aws": 3,
        "azure": 3,
        "deployment": 2,
        "vercel": 1,
        "react": 1,
        "next.js": 1,
        "nextjs": 1,
    }

    for signal, points in signals.items():
        if signal in text:
            score += points
            matched.append(signal)

    score = min(score, 15)

    breakdown.cloud_fullstack = score

    if matched:
        breakdown.reasons.append(
            "Cloud/full-stack evidence: "
            + ", ".join(matched[:8])
        )


def score_engineering_depth(
    resume: ResumeData,
    breakdown: ScoreBreakdown,
) -> None:
    """
    Maximum: 5 points.

    Rewards non-trivial engineering practices.
    """

    text = resume.raw_text.lower()

    score = 0
    matched = []

    signals = {
        "testing": 1,
        "unit test": 1,
        "pytest": 1,
        "caching": 1,
        "queue": 1,
        "observability": 1,
        "logging": 1,
        "concurrency": 1,
        "ci/cd": 1,
        "failure handling": 1,
        "architecture": 1,
    }

    for signal, points in signals.items():
        if signal in text and score < 5:
            score += points
            matched.append(signal)

    breakdown.engineering_depth = score

    if matched:
        breakdown.reasons.append(
            "Engineering depth: " + ", ".join(matched)
        )


def calculate_score(resume, llm_analysis: LLMAnalysis | None = None):
    breakdown = ScoreBreakdown()

    score_ai_project_depth(resume, breakdown)
    score_python_backend(resume, breakdown)
    score_cloud_fullstack(resume, breakdown)
    score_engineering_depth(resume, breakdown)

    if llm_analysis is not None:
        breakdown.ai_project_depth = llm_analysis.ai_project_score

        breakdown.reasons.append(
            f"LLM project-quality assessment: "
            f"{llm_analysis.ai_project_score}/40"
        )

        breakdown.strengths.extend(
            llm_analysis.strengths
        )

        breakdown.concerns.extend(
            llm_analysis.concerns
        )

    breakdown.github = 0

    return breakdown