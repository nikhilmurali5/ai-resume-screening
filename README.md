# AI Resume Screening & Ranking System

An AI-powered resume screening system that processes PDF resumes, filters candidates based on Python + AI experience, scores eligible candidates, enriches GitHub information, and generates ranked results.

## Features

- PDF resume parsing
- Python + AI eligibility filtering
- Groq LLM-based AI project analysis
- Hybrid candidate scoring
- GitHub enrichment
- Ranked JSON output
- Simple Streamlit UI
- Unit tests

## Architecture

```text
                    PDF Resumes
                         │
                         ▼
                ┌─────────────────┐
                │   PDF Parser    │
                │     pypdf       │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │   Eligibility   │
                │  Python + AI    │
                └────────┬────────┘
                         │
                    Eligible
                         │
                         ▼
                ┌─────────────────┐
                │   Groq LLM      │
                │ Project Analysis│
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │     Scoring     │
                │     /100        │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ GitHub Enrichment│
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Ranked Results  │
                │  results.json  │
                └─────────────────┘
```

## Project Structure

```text
ai-resume-screening/
│
├── resumes/                 # Input PDF resumes
├── src/
│   ├── config.py            # Configuration
│   ├── models.py            # Data models
│   ├── parser.py            # PDF parsing
│   ├── eligibility.py       # Eligibility filtering
│   ├── scorer.py            # Scoring logic
│   ├── llm.py               # Groq LLM analysis
│   ├── github.py            # GitHub enrichment
│   ├── pipeline.py          # Pipeline components
│   └── main.py              # CLI entry point
├── tests/
│   ├── test_eligibility.py
│   └── test_scorer.py
├── output/
│   └── results.json
├── docs/                    # README screenshots
├── app.py                   # Streamlit UI
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Scoring

| Category | Maximum |
|---|---:|
| AI Project Depth | 40 |
| Python / Backend | 30 |
| Cloud / Full Stack | 15 |
| GitHub | 10 |
| Engineering Depth | 5 |
| **Total** | **100** |

A candidate must demonstrate both **Python** and **AI/LLM/RAG/Agentic experience** to be eligible.

## Steps to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Create `.env`:

```env
GROQ_API_KEY=your_api_key
GROQ_MODEL=openai/gpt-oss-120b
```

### 3. Add resumes

Place PDF resumes inside:

```text
resumes/
```

### 4. Run the screening pipeline

```bash
python -m src.main --input resumes --output output/results.json
```

### 5. Run the Streamlit UI

```bash
streamlit run app.py
```

### 6. Run tests

```bash
pytest -q
```

## Sample Result

```text
Total resumes      : 50
Successfully parsed: 50
Eligible           : 39
Rejected           : 11
Failed/unreadable  : 0
LLM enabled        : True
LLM analyzed       : 39
```

## Streamlit Interface

### Resume Upload

![Resume Upload](docs/streamlit-upload.png)

### Screening Summary & Ranked Candidates

![Screening Summary](docs/streamlit-summary.png)

### Candidate Details & Score Breakdown

![Candidate Details](docs/streamlit-candidate-details.png)

### Rejected Candidates

![Rejected Candidates](docs/streamlit-rejected.png)

## Output

Results are generated at:

```text
output/results.json
```

The output contains candidate ranking, score breakdown, skills, project summary, GitHub information, strengths, concerns, and LLM analysis.

## Technologies

Python • Pydantic • pypdf • Groq • GitHub API • Pytest • Streamlit

## Author

**Nikhil Murali**
