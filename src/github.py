import re
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests


GITHUB_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?github\.com/([A-Za-z0-9-]+)",
    re.IGNORECASE,
)


def extract_github_username(github_url: Optional[str]) -> Optional[str]:
    if not github_url:
        return None

    match = GITHUB_URL_PATTERN.search(github_url)

    if not match:
        return None

    return match.group(1)


def enrich_github(github_url: Optional[str]) -> dict:
    """
    Fetch lightweight public GitHub information.

    Returns a safe result even when GitHub is unavailable.
    """

    username = extract_github_username(github_url)

    if not username:
        return {
            "available": False,
            "score": 0,
            "summary": "No GitHub profile found",
            "error": None,
        }

    try:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "ai-resume-screening-assignment",
        }

        profile_response = requests.get(
            f"https://api.github.com/users/{username}",
            headers=headers,
            timeout=5,
        )

        if profile_response.status_code != 200:
            return {
                "available": False,
                "score": 0,
                "summary": "GitHub profile unavailable",
                "error": f"HTTP {profile_response.status_code}",
            }

        profile = profile_response.json()

        repos_response = requests.get(
            f"https://api.github.com/users/{username}/repos",
            params={
                "per_page": 100,
                "sort": "updated",
            },
            headers=headers,
            timeout=5,
        )

        if repos_response.status_code != 200:
            return {
                "available": True,
                "score": 0,
                "summary": "GitHub profile found but repositories unavailable",
                "error": f"HTTP {repos_response.status_code}",
            }

        repos = repos_response.json()

        now = datetime.now(timezone.utc)
        recent_cutoff = now - timedelta(days=180)

        recent_repos = 0
        relevant_repos = 0

        relevant_terms = {
            "python",
            "ai",
            "ml",
            "machine-learning",
            "deep-learning",
            "llm",
            "rag",
            "agent",
            "langchain",
            "langgraph",
            "fastapi",
            "tensorflow",
            "pytorch",
        }

        for repo in repos:
            updated_at = repo.get("updated_at")

            if updated_at:
                try:
                    updated = datetime.fromisoformat(
                        updated_at.replace("Z", "+00:00")
                    )

                    if updated >= recent_cutoff:
                        recent_repos += 1
                except ValueError:
                    pass

            repo_text = " ".join(
                [
                    repo.get("name") or "",
                    repo.get("description") or "",
                    repo.get("language") or "",
                ]
            ).lower()

            if any(term in repo_text for term in relevant_terms):
                relevant_repos += 1

        # 0–5 points for recent activity
        activity_score = min(recent_repos, 5)

        # 0–5 points for maintained/relevant repositories
        repository_score = min(relevant_repos, 5)

        total_score = activity_score + repository_score

        return {
            "available": True,
            "score": min(total_score, 10),
            "summary": (
                f"{recent_repos} recently updated repositories; "
                f"{relevant_repos} Python/AI/backend-relevant repositories."
            ),
            "error": None,
        }

    except requests.RequestException as exc:
        return {
            "available": False,
            "score": 0,
            "summary": "GitHub enrichment failed",
            "error": str(exc),
        }

    except Exception as exc:
        return {
            "available": False,
            "score": 0,
            "summary": "Unexpected GitHub enrichment error",
            "error": str(exc),
        }