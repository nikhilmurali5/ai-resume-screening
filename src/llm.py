from typing import List

from pydantic import BaseModel, Field
from groq import Groq

from src.config import GROQ_API_KEY, GROQ_MODEL


class LLMAnalysis(BaseModel):
    ai_project_score: int = Field(ge=0, le=40)
    project_summary: str = "No project summary provided by the model."
    implementation_evidence: List[str] = Field(
        default_factory=list
    )
    strengths: List[str] = Field(
        default_factory=list
    )
    concerns: List[str] = Field(
        default_factory=list
    )


SYSTEM_PROMPT = """
You are an expert technical recruiter evaluating software
engineering internship resumes.

Evaluate ONLY the evidence present in the supplied resume.

Focus specifically on the quality and depth of
AI/LLM/RAG/agentic projects.

Scoring guidance for ai_project_score (0-40):

- 0-10: weak, mostly keyword/tutorial exposure
- 11-20: basic practical AI project
- 21-30: solid implementation with meaningful engineering
- 31-40: strong production-like AI/agentic/RAG implementation

Reward:

- RAG pipelines
- retrieval/vector search
- embeddings
- tool calling
- multi-agent workflows
- LangGraph/state/orchestration
- evaluation
- meaningful backend/business logic
- clear implementation ownership

Penalize:

- simple chatbot projects
- thin LLM/API wrappers
- tutorial-style projects
- framework names without implementation evidence

Do not invent technologies, projects, or experience.

Return concise, evidence-based reasoning.

Your response MUST be valid JSON matching the requested schema.
Return JSON only.
"""


def analyze_resume_with_llm(
    resume_text: str,
) -> LLMAnalysis | None:

    if not GROQ_API_KEY:
        return None

    try:
        client = Groq(
            api_key=GROQ_API_KEY
        )

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        "Analyze this resume and return "
                        "the result as JSON.\n\n"
                        f"{resume_text[:12000]}"
                    ),
                },
            ],
            response_format={
                "type": "json_object",
            },
        )

        content = response.choices[0].message.content

        if not content:
            return None

        return LLMAnalysis.model_validate_json(
            content
        )

    except Exception as exc:
        print(
            f"LLM analysis failed: "
            f"{type(exc).__name__}: {exc}"
        )
        return None