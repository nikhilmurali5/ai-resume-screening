from typing import List, Optional
from pydantic import BaseModel, Field


class ResumeData(BaseModel):
    """Structured information extracted from a resume."""

    filename: str
    raw_text: str

    candidate_name: str = "Unknown"
    email: Optional[str] = None
    github_url: Optional[str] = None

    skills: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)
    experience: List[str] = Field(default_factory=list)


class ParseResult(BaseModel):
    """Result of parsing one resume."""

    success: bool
    filename: str

    resume: Optional[ResumeData] = None
    error: Optional[str] = None