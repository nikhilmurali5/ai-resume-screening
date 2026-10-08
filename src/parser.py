import re
from pathlib import Path
from typing import Optional

from pypdf import PdfReader

from .models import ParseResult, ResumeData


EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

GITHUB_PATTERN = re.compile(
    r"https?://(?:www\.)?github\.com/[A-Za-z0-9_.-]+/?",
    re.IGNORECASE,
)


def extract_pdf_text(pdf_path: Path) -> str:
    """
    Extract text from a PDF.

    Raises an exception when the PDF cannot be read so the caller
    can handle the failure without stopping the complete batch.
    """
    reader = PdfReader(str(pdf_path))

    pages = []

    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)

    return "\n".join(pages).strip()


def extract_email(text: str) -> Optional[str]:
    match = EMAIL_PATTERN.search(text)

    if match:
        return match.group(0)

    return None


def extract_github_url(text: str) -> Optional[str]:
    match = GITHUB_PATTERN.search(text)

    if match:
        return match.group(0).rstrip("/")

    return None


def extract_candidate_name(text: str, filename: str) -> str:
    """
    Extract the candidate name from the beginning of a resume.

    The parser handles:
    - Normal names
    - ALL CAPS names
    - Names followed immediately by Email/Mobile information
    - Names followed by phone numbers
    - Common resume section headings
    - Contact information and URLs

    If no reliable name is found, the PDF filename is used as a fallback.
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return Path(filename).stem

    ignored_exact = {
        "resume",
        "curriculum vitae",
        "cv",
        "profile",
        "summary",
        "summar y",
        "professional summary",
        "professional experience",
        "experience",
        "education",
        "skills",
        "technical skills",
        "skills summary",
        "projects",
        "certifications",
        "achievements",
        "internship",
        "contact",
    }

    ignored_terms = {
        "linkedin",
        "github",
        "http://",
        "https://",
        "www.",
        "mobile",
        "phone",
        "email",
        "gmail.com",
        "outlook.com",
    }

    for line in lines[:15]:
        cleaned = line.strip()
        lower = cleaned.lower()

        # Ignore obvious headings.
        if lower in ignored_exact:
            continue

        # ---------------------------------------------------------
        # Handle names concatenated with contact information.
        #
        # Examples:
        # "Vaibhav WakdeEmail: vaibhavwakde@gmail.com"
        # "Prathamesh Patil+91 73490 41840"
        # ---------------------------------------------------------

        contact_match = re.split(
            r"email:|mobile:|phone:|\+91|\b\d{10}\b",
            cleaned,
            flags=re.IGNORECASE,
        )

        candidate_part = contact_match[0].strip(" -|,:")

        if candidate_part and candidate_part != cleaned:
            cleaned = candidate_part
            lower = cleaned.lower()

        # Ignore empty values after cleaning.
        if not cleaned:
            continue

        # Ignore contact/profile information.
        if any(term in lower for term in ignored_terms):
            continue

        # Ignore email addresses.
        if EMAIL_PATTERN.search(cleaned):
            continue

        # Ignore URLs.
        if "linkedin.com" in lower or "github.com" in lower:
            continue

        # Ignore phone-number-like lines.
        digit_count = sum(
            character.isdigit()
            for character in cleaned
        )

        if digit_count >= 3:
            continue

        # Ignore contact/header separators.
        if "|" in cleaned or "—" in cleaned:
            continue

        words = cleaned.split()

        # Candidate names are normally 2–5 words.
        if not 2 <= len(words) <= 5:
            continue

        if len(cleaned) > 50:
            continue

        # Accept:
        #   JOHN DOE
        #   John Doe
        #   V Sree Raghu Vardhan
        #
        # Reject sentence-like text.
        is_all_upper = cleaned.upper() == cleaned

        is_name_case = all(
            word[0].isupper()
            for word in words
            if word
        )

        if not (is_all_upper or is_name_case):
            continue

        # Words should contain alphabetic characters.
        # Allow periods, apostrophes and hyphens for names such as:
        # NISARGA H. S.
        # O'Connor
        # Mary-Jane
        valid_name = all(
            word
            .replace(".", "")
            .replace("'", "")
            .replace("-", "")
            .isalpha()
            for word in words
        )

        if not valid_name:
            continue

        return cleaned

    # Safe fallback when the parser cannot confidently identify a name.
    return Path(filename).stem


def extract_skills(text: str) -> list[str]:
    """
    Lightweight skill extraction.

    The final ranking logic distinguishes genuine evidence
    from skills that only appear as keywords.
    """

    known_skills = [
        "Python",
        "FastAPI",
        "Flask",
        "Django",
        "Java",
        "JavaScript",
        "TypeScript",
        "React",
        "Next.js",
        "Node.js",
        "PostgreSQL",
        "MySQL",
        "Redis",
        "Docker",
        "GCP",
        "AWS",
        "Azure",
        "TensorFlow",
        "PyTorch",
        "Keras",
        "OpenCV",
        "LangChain",
        "LangGraph",
        "LlamaIndex",
        "RAG",
        "LLM",
        "Git",
        "GitHub",
        "SQL",
    ]

    text_lower = text.lower()

    matched = []

    for skill in known_skills:
        if skill.lower() in text_lower:
            matched.append(skill)

    return matched


def parse_resume(pdf_path: Path) -> ParseResult:
    """
    Parse one PDF resume.

    Any failure is converted into a ParseResult instead of
    crashing the complete screening batch.
    """

    try:
        text = extract_pdf_text(pdf_path)

        if not text.strip():
            return ParseResult(
                success=False,
                filename=pdf_path.name,
                error="PDF contains no extractable text",
            )

        resume = ResumeData(
            filename=pdf_path.name,
            raw_text=text,
            candidate_name=extract_candidate_name(
                text,
                pdf_path.name,
            ),
            email=extract_email(text),
            github_url=extract_github_url(text),
            skills=extract_skills(text),
        )

        return ParseResult(
            success=True,
            filename=pdf_path.name,
            resume=resume,
        )

    except Exception as exc:
        return ParseResult(
            success=False,
            filename=pdf_path.name,
            error=f"{type(exc).__name__}: {exc}",
        )