import json
import shutil
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from src.main import screen_resumes


st.set_page_config(
    page_title="AI Resume Screening",
    page_icon="📄",
    layout="wide",
)


# -----------------------------
# Simple Styling
# -----------------------------

st.title("📄 AI Resume Screening")
st.caption(
    "AI-powered resume screening and ranking using rule-based eligibility, "
    "LLM analysis, and GitHub enrichment."
)

st.divider()


# -----------------------------
# Upload Section
# -----------------------------

st.subheader("Upload Resumes")

uploaded_files = st.file_uploader(
    "Upload PDF resumes",
    type=["pdf"],
    accept_multiple_files=True,
)

if uploaded_files:

    st.info(f"{len(uploaded_files)} resume(s) uploaded.")

    if st.button(
        "🚀 Screen Resumes",
        type="primary",
        use_container_width=True,
    ):

        with st.spinner(
            "Processing resumes, running eligibility checks, "
            "LLM analysis and GitHub enrichment..."
        ):

            temp_dir = Path(
                tempfile.mkdtemp(prefix="resume_screening_")
            )

            try:
                # Save uploaded PDFs temporarily
                for uploaded_file in uploaded_files:
                    file_path = temp_dir / uploaded_file.name

                    with open(file_path, "wb") as file:
                        file.write(uploaded_file.getbuffer())

                # Run existing screening pipeline
                results = screen_resumes(temp_dir)

                # Store results in session
                st.session_state["results"] = results

            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)


# -----------------------------
# Results
# -----------------------------

if "results" in st.session_state:

    results = st.session_state["results"]
    summary = results["batch_summary"]

    st.divider()

    st.subheader("Screening Summary")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Resumes",
        summary["total_resumes"],
    )

    col2.metric(
        "Eligible",
        summary["eligible"],
    )

    col3.metric(
        "Rejected",
        summary["rejected"],
    )

    col4.metric(
        "Failed",
        summary["failed_or_unreadable"],
    )

    st.divider()

    # -----------------------------
    # Ranked Candidates
    # -----------------------------

    st.subheader("🏆 Ranked Candidates")

    candidates = results["ranked_candidates"]

    if candidates:

        table_data = []

        for candidate in candidates:
            table_data.append(
                {
                    "Rank": candidate["rank"],
                    "Candidate": candidate["candidate_name"],
                    "Score": candidate["total_score"],
                    "AI / LLM": candidate["score_breakdown"][
                        "ai_project_depth"
                    ],
                    "Python / Backend": candidate["score_breakdown"][
                        "python_backend"
                    ],
                    "Cloud / Full Stack": candidate["score_breakdown"][
                        "cloud_fullstack"
                    ],
                    "GitHub": candidate["score_breakdown"]["github"],
                    "Engineering": candidate["score_breakdown"][
                        "engineering_depth"
                    ],
                }
            )

        df = pd.DataFrame(table_data)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        # -----------------------------
        # Candidate Details
        # -----------------------------

        st.subheader("Candidate Details")

        candidate_names = [
            candidate["candidate_name"]
            for candidate in candidates
        ]

        selected_name = st.selectbox(
            "Select a candidate",
            candidate_names,
        )

        selected = next(
            candidate
            for candidate in candidates
            if candidate["candidate_name"] == selected_name
        )

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                f"### {selected['candidate_name']}"
            )

            st.write(
                f"**Overall Score:** "
                f"{selected['total_score']}/100"
            )

            st.write(
                f"**Resume:** "
                f"{selected['filename']}"
            )

            st.write(
                f"**Skills:** "
                f"{', '.join(selected['matched_skills']) or 'None detected'}"
            )

        with col2:
            st.markdown("### Score Breakdown")

            breakdown = selected["score_breakdown"]

            st.write(
                f"**AI Project Depth:** "
                f"{breakdown['ai_project_depth']}/40"
            )

            st.write(
                f"**Python / Backend:** "
                f"{breakdown['python_backend']}/30"
            )

            st.write(
                f"**Cloud / Full Stack:** "
                f"{breakdown['cloud_fullstack']}/15"
            )

            st.write(
                f"**GitHub:** "
                f"{breakdown['github']}/10"
            )

            st.write(
                f"**Engineering Depth:** "
                f"{breakdown['engineering_depth']}/5"
            )

        st.markdown("### Project Summary")

        st.write(
            selected.get(
                "project_summary",
                "No project summary available.",
            )
        )

        st.markdown("### Strengths")

        strengths = selected.get("strengths", [])

        if strengths:
            for strength in strengths:
                st.write(f"✅ {strength}")
        else:
            st.write("No additional strengths identified.")

        st.markdown("### Concerns")

        concerns = selected.get("concerns", [])

        if concerns:
            for concern in concerns:
                st.write(f"⚠️ {concern}")
        else:
            st.write("No major concerns identified.")

        st.markdown("### GitHub")

        github = selected["github"]

        if github["available"]:
            st.write(
                f"**GitHub Score:** "
                f"{github['score']}/10"
            )
            st.write(github["summary"])
        else:
            st.write("No public GitHub profile found.")

        st.markdown("### LLM Analysis")

        llm = selected["llm_analysis"]

        if llm["used"]:
            st.success(
                f"LLM analysis used — "
                f"AI project score: "
                f"{llm['ai_project_score']}/40"
            )

            evidence = llm.get(
                "implementation_evidence",
                [],
            )

            if evidence:
                st.write("**Implementation Evidence:**")

                for item in evidence:
                    st.write(f"• {item}")
        else:
            st.warning(
                "LLM analysis was unavailable. "
                "Deterministic scoring was used."
            )

    else:
        st.warning("No eligible candidates found.")

    # -----------------------------
    # Rejected Candidates
    # -----------------------------

    if results["rejected_candidates"]:

        st.divider()

        st.subheader("Rejected Candidates")

        rejected_data = []

        for candidate in results["rejected_candidates"]:
            rejected_data.append(
                {
                    "Candidate": candidate["candidate_name"],
                    "Resume": candidate["filename"],
                    "Reason": "; ".join(
                        candidate["rejection_reasons"]
                    ),
                }
            )

        rejected_df = pd.DataFrame(rejected_data)

        st.dataframe(
            rejected_df,
            use_container_width=True,
            hide_index=True,
        )

    # -----------------------------
    # Download JSON
    # -----------------------------

    st.divider()

    json_data = json.dumps(
        results,
        indent=2,
        ensure_ascii=False,
    )

    st.download_button(
        label="⬇️ Download results.json",
        data=json_data,
        file_name="results.json",
        mime="application/json",
        use_container_width=True,
    )