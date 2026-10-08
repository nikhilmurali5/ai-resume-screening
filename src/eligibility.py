from dataclasses import dataclass
from typing import List

from .models import ResumeData


PYTHON_SIGNALS = {
    "python",
    "fastapi",
    "flask",
    "django",
    "tensorflow",
    "pytorch",
    "keras",
}

AI_SIGNALS = {
    "langchain",
    "langgraph",
    "llamaindex",
    "rag",
    "llm",
    "agentic",
    "agent",
    "multi-agent",
    "embeddings",
    "vector search",
    "vector database",
    "tool calling",
    "tool-calling",
    "retrieval augmented generation",
    "generative ai",
    "generative ai",
    "google adk",
}


@dataclass
class EligibilityResult:
    eligible: bool
    rejection_reasons: List[str]
    matched_skills: List[str]
    python_evidence: List[str]
    ai_evidence: List[str]


def _find_signals(text: str, signals: set[str]) -> List[str]:
    text_lower = text.lower()

    return [
        signal
        for signal in signals
        if signal in text_lower
    ]


def check_eligibility(resume: ResumeData) -> EligibilityResult:
    """
    Apply the assignment's hard eligibility rules.

    A candidate must have:
    1. Python evidence
    2. AI/LLM/RAG/agentic evidence

    This intentionally happens before scoring.
    """

    text = resume.raw_text

    python_evidence = _find_signals(
        text,
        PYTHON_SIGNALS,
    )

    ai_evidence = _find_signals(
        text,
        AI_SIGNALS,
    )

    rejection_reasons = []

    if not python_evidence:
        rejection_reasons.append(
            "No evidence of Python stack"
        )

    if not ai_evidence:
        rejection_reasons.append(
            "No evidence of AI/LLM/RAG/agentic work"
        )

    return EligibilityResult(
        eligible=not rejection_reasons,
        rejection_reasons=rejection_reasons,
        matched_skills=resume.skills,
        python_evidence=python_evidence,
        ai_evidence=ai_evidence,
    )