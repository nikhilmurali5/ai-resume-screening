import argparse
import json
from pathlib import Path

from src.eligibility import check_eligibility
from src.github import enrich_github
from src.llm import analyze_resume_with_llm
from src.parser import parse_resume
from src.scorer import calculate_score


def screen_resumes(input_dir: Path) -> dict:
    pdf_files = sorted(input_dir.glob("*.pdf"))

    eligible_candidates = []
    rejected_candidates = []
    failed_candidates = []

    for pdf_file in pdf_files:
        result = parse_resume(pdf_file)

        if not result.success:
            failed_candidates.append(
                {
                    "filename": pdf_file.name,
                    "error": result.error,
                }
            )
            continue

        resume = result.resume

        # ---------------------------------------------------------
        # HARD ELIGIBILITY FILTER
        # ---------------------------------------------------------
        eligibility = check_eligibility(resume)

        if not eligibility.eligible:
            rejected_candidates.append(
                {
                    "candidate_name": resume.candidate_name,
                    "filename": resume.filename,
                    "eligible": False,
                    "rejection_reasons": eligibility.rejection_reasons,
                    "matched_skills": resume.skills,
                }
            )
            continue

        # ---------------------------------------------------------
        # LLM ANALYSIS
        # ---------------------------------------------------------
        llm_analysis = analyze_resume_with_llm(
            resume.raw_text
        )

        # ---------------------------------------------------------
        # DETERMINISTIC + LLM SCORING
        # ---------------------------------------------------------
        score = calculate_score(
            resume,
            llm_analysis=llm_analysis,
        )

        # ---------------------------------------------------------
        # GITHUB ENRICHMENT
        # ---------------------------------------------------------
        github = enrich_github(
            resume.github_url
        )

        score.github = github["score"]

        # ---------------------------------------------------------
        # PROJECT SUMMARY
        # ---------------------------------------------------------
        if llm_analysis:
            project_summary = (
                llm_analysis.project_summary
            )
        else:
            project_summary = build_project_summary(
                resume
            )

        # ---------------------------------------------------------
        # CANDIDATE RESULT
        # ---------------------------------------------------------
        candidate = {
            "candidate_name": resume.candidate_name,
            "filename": resume.filename,
            "eligible": True,

            "total_score": score.total,

            "score_breakdown": {
                "ai_project_depth": score.ai_project_depth,
                "python_backend": score.python_backend,
                "cloud_fullstack": score.cloud_fullstack,
                "github": score.github,
                "engineering_depth": score.engineering_depth,
            },

            "matched_skills": resume.skills,

            "project_summary": project_summary,

            "github": {
                "url": resume.github_url,
                "available": github["available"],
                "score": github["score"],
                "summary": github["summary"],
                "error": github["error"],
            },

            "strengths": score.strengths,

            "concerns": score.concerns,

            "evidence": score.reasons,

            # Explicitly expose AI usage in output
            "llm_analysis": {
                "used": llm_analysis is not None,
                "ai_project_score": (
                    llm_analysis.ai_project_score
                    if llm_analysis
                    else None
                ),
                "implementation_evidence": (
                    llm_analysis.implementation_evidence
                    if llm_analysis
                    else []
                ),
            },
        }

        eligible_candidates.append(candidate)

    # -------------------------------------------------------------
    # SORT BY FINAL SCORE
    # -------------------------------------------------------------
    eligible_candidates.sort(
        key=lambda candidate: candidate["total_score"],
        reverse=True,
    )

    # -------------------------------------------------------------
    # ASSIGN RANK
    # -------------------------------------------------------------
    for rank, candidate in enumerate(
        eligible_candidates,
        start=1,
    ):
        candidate["rank"] = rank

    # -------------------------------------------------------------
    # BATCH SUMMARY
    # -------------------------------------------------------------
    return {
        "batch_summary": {
            "total_resumes": len(pdf_files),
            "successfully_parsed": (
                len(pdf_files)
                - len(failed_candidates)
            ),
            "eligible": len(eligible_candidates),
            "rejected": len(rejected_candidates),
            "failed_or_unreadable": len(
                failed_candidates
            ),
            "llm_enabled": any(
                candidate["llm_analysis"]["used"]
                for candidate in eligible_candidates
            ),
            "llm_analyzed_candidates": sum(
                1
                for candidate in eligible_candidates
                if candidate["llm_analysis"]["used"]
            ),
        },

        "ranked_candidates": eligible_candidates,

        "rejected_candidates": rejected_candidates,

        "failed_candidates": failed_candidates,
    }


def build_project_summary(resume) -> str:
    """
    Fallback project summary used when the LLM is unavailable.

    The summary is extracted directly from the resume
    without inventing project information.
    """

    text = resume.raw_text.replace(
        "\n",
        " ",
    )

    sentences = [
        sentence.strip()
        for sentence in text.split(".")
        if sentence.strip()
    ]

    project_keywords = [
        "project",
        "built",
        "developed",
        "implemented",
        "created",
        "rag",
        "agent",
        "langchain",
        "langgraph",
        "fastapi",
    ]

    matches = []

    for sentence in sentences:
        sentence_lower = sentence.lower()

        if any(
            keyword in sentence_lower
            for keyword in project_keywords
        ):
            matches.append(sentence)

        if len(matches) == 2:
            break

    if matches:
        summary = ". ".join(matches)
        return summary[:500]

    return "No detailed project summary extracted."


def main():
    parser = argparse.ArgumentParser(
        description="AI Resume Screening & Ranking System"
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Directory containing resume PDFs",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Output JSON path",
    )

    args = parser.parse_args()

    input_dir = Path(args.input)
    output_path = Path(args.output)

    if not input_dir.exists():
        raise SystemExit(
            f"Input directory does not exist: {input_dir}"
        )

    # -------------------------------------------------------------
    # RUN SCREENING PIPELINE
    # -------------------------------------------------------------
    result = screen_resumes(input_dir)

    # -------------------------------------------------------------
    # WRITE JSON
    # -------------------------------------------------------------
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            result,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # -------------------------------------------------------------
    # TERMINAL SUMMARY
    # -------------------------------------------------------------
    summary = result["batch_summary"]

    print("\n" + "=" * 60)
    print("AI RESUME SCREENING COMPLETE")
    print("=" * 60)

    print(
        f"Total resumes      : "
        f"{summary['total_resumes']}"
    )

    print(
        f"Successfully parsed: "
        f"{summary['successfully_parsed']}"
    )

    print(
        f"Eligible           : "
        f"{summary['eligible']}"
    )

    print(
        f"Rejected           : "
        f"{summary['rejected']}"
    )

    print(
        f"Failed/unreadable  : "
        f"{summary['failed_or_unreadable']}"
    )

    print(
        f"LLM enabled        : "
        f"{summary['llm_enabled']}"
    )

    print(
        f"LLM analyzed       : "
        f"{summary['llm_analyzed_candidates']}"
    )

    print(
        f"\nResults written to: "
        f"{output_path}"
    )

    # -------------------------------------------------------------
    # TOP 10
    # -------------------------------------------------------------
    print("\nTop 10 Candidates")
    print("-" * 60)

    for candidate in result[
        "ranked_candidates"
    ][:10]:

        print(
            f"{candidate['rank']:>2}. "
            f"{candidate['candidate_name'][:30]:<30} "
            f"{candidate['total_score']:>3}/100"
        )


if __name__ == "__main__":
    main()