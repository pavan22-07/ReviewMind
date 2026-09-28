# ReviewMind 🧠

> *"A Code Review Agent that learns how your team reviews code."*

---

## 1. Problem Statement

Every software engineering team gradually evolves a distinct culture of code quality. Over months and years, teams establish:
- **Team coding standards** and stylistic policies
- **Recurring mistakes** caught repeatedly across pull requests
- **Architectural preferences** (e.g. strict layering, service-layer patterns, specific ORM usage)
- **Hard-won lessons** learned from past production outages, security audits, and retrospectives

However, this critical institutional knowledge remains fragmented—buried in scattered documentation, past GitHub pull request comments, Slack channels, or simply inside senior engineers' heads.

## 2. Why Generic Code Review Is Insufficient

While modern AI code review tools are proficient at detecting generic syntax errors, standard linting violations, and textbook algorithmic flaws, they treat each code review as an isolated, stateless event. They lack **persistent organizational memory that accumulates and recalls team-specific review knowledge across review sessions**.

As a result:
- The team repeatedly receives generic recommendations rather than organization-aligned guidance.
- Known anti-patterns slip past reviews because the AI reviewer does not remember past team decisions.
- Senior engineers must continually repeat the exact same feedback on pull requests.

## 3. Proposed Solution: ReviewMind

**ReviewMind** is an intelligent Code Review Agent built with **Hindsight** as its persistent organizational memory layer and **Groq** as its high-speed inference engine.

ReviewMind operationalizes a closed-loop review lifecycle:
1. **Recall**: When code is submitted, ReviewMind queries Hindsight to recall relevant team standards, known mistakes, and historical review lessons.
2. **Review**: ReviewMind sends the code and recalled team memories to the LLM (`openai/gpt-oss-120b` via Groq) with instructions to enforce organizational conventions while distinguishing them from general best practices.
3. **Report**: Findings are displayed in structured JSON with severity levels, affected lines, explanations, code suggestions, and explicit citations of which team rules were applied.
4. **Learn**: Reusable engineering lessons are synthesized from the review findings.
5. **Retain**: Extracted lessons are stored back into Hindsight with structured metadata and tags, ensuring the entire engineering team benefits in subsequent reviews.

---

## 4. System Architecture

```
                 Developer
                     │
                     ▼
                Streamlit UI
                     │
                     ▼
              ReviewMind Agent
                 /        \
                /          \
               ▼            ▼
        Hindsight (Recall)   Groq LLM (openai/gpt-oss-120b)
               │            │
               └─────┬──────┘
                     │
                     ▼
             Structured Review
        (Issues, Risk, Rules Used)
                     │
                     ▼
             Learning Extraction
                     │
                     ▼
             Hindsight (Retain)
        (Accumulated for future reviews)
```

---

## 5. Hindsight's Role

Hindsight is the central, stateful memory foundation of ReviewMind:
- **Dedicated Team Memory Bank**: ReviewMind provisions a dedicated bank (`HINDSIGHT_BANK_ID`) for the engineering team.
- **Semantic Memory Recall**: Maps arbitrary source code, keywords, and patterns to relevant team policies via semantic similarity search.
- **Multi-Domain Knowledge**: Retains 4 core types of team knowledge:
  1. *Team Standards* (e.g. mandatory parameterized queries, input validation)
  2. *Common Mistakes* (e.g. leaking raw exceptions to HTTP callers)
  3. *Architectural Preferences* (e.g. keeping business logic out of controllers)
  4. *Previous Review Lessons* (lessons extracted from previous code reviews)
- **Continuous Retention**: Newly extracted review insights are saved back into Hindsight with structured tags (`language`, `category`, `source`) and metadata.

---

## 6. Technology Stack

- **Frontend & Interface**: [Streamlit](https://streamlit.io/)
- **Organizational Memory**: [Hindsight](https://hindsight.vectorize.io) via official `hindsight-client` Python SDK
- **LLM Inference Provider**: [Groq](https://groq.com) via official `groq` Python SDK
- **Default LLM Model**: `openai/gpt-oss-120b` (configurable via `GROQ_MODEL`)
- **Data Validation & Schemas**: Pydantic v2
- **Configuration & Environment**: `python-dotenv`

---

## 7. Project Structure

```
ReviewMind/
│
├── app.py                  # Main Streamlit web application
├── demo_samples.py         # Realistic educational demo samples & vulnerability scenarios
├── requirements.txt        # Python package dependencies
├── .env.example            # Template for environment variables
├── .gitignore              # Files excluded from version control
├── README.md               # Comprehensive documentation
│
└── src/
    ├── __init__.py         # Package exports
    ├── config.py           # Configuration management and settings validation
    ├── models.py           # Pydantic schemas for issues, reviews, and memories
    ├── memory.py           # Hindsight memory management (recall, retain, seed)
    ├── prompts.py          # Prompt engineering templates for review and memory grounding
    └── reviewer.py         # ReviewMind orchestrator combining Hindsight recall and Groq LLM
```

---

## 8. Installation

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- Pip package manager

### Steps
1. Navigate to the project directory:
   ```bash
   cd ReviewMind
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## 9. Environment Variables

Create a `.env` file in the `ReviewMind` directory:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Groq API Key (Required for LLM code review inference)
GROQ_API_KEY=gsk_your_groq_api_key_here

# Hindsight Configuration (Required for organizational memory)
HINDSIGHT_API_KEY=your_hindsight_api_key_here
HINDSIGHT_API_URL=https://api.hindsight.vectorize.io
HINDSIGHT_BANK_ID=reviewmind-team

# Default LLM Model on Groq
GROQ_MODEL=openai/gpt-oss-120b
```

> **Note:** API keys can also be configured or updated dynamically in the application's sidebar settings.

---

## 10. Running the Application

Launch the Streamlit app with:

```bash
streamlit run app.py
```

The web interface will open at:
```
http://localhost:8501
```

---

## 11. Demo Workflow (The Hackathon Walkthrough)

To experience the core differentiation between generic AI review and memory-augmented review:

### Step 1: Seed Foundational Team Standards
1. Open the **Team Memory (Hindsight)** tab.
2. Click **🌱 Seed Standards Now**.
3. This populates Hindsight with four baseline standards:
   - SQL Parameterization Standard
   - Exception Sanitization Rule
   - Controller/Service Layer Architecture Preference
   - Input Validation Policy

### Step 2: Run Review Without Memory (Generic Baseline)
1. Navigate to the **Review Code** tab.
2. Under **Load Demo Sample**, select `1. SQL Injection (String Concatenation in Query)`.
3. Set Review Mode to **⚡ Generic Review (Without Memory)**.
4. Click **🚀 Run ReviewMind Review**.
5. Notice that the generic review flags the syntax flaw, but **applies 0 team memory rules**.

### Step 3: Run Review With Memory (Hindsight Active)
1. Switch Review Mode to **🧠 With Team Memory (Hindsight)**.
2. Click **🚀 Run ReviewMind Review**.
3. Notice:
   - ReviewMind queries Hindsight and recalls the exact SQL coding standard.
   - The green card **🛡️ Team Memory Applied (From Hindsight)** explicitly cites the team standard.
   - The LLM enforces the team-approved query pattern.
   - Under **🎓 Continuous Learning Loop**, newly extracted lessons are stored back into Hindsight for the team.

### Step 4: Compare Side-by-Side
1. Go to the **🧪 Interactive Demo Walkthrough** tab.
2. Run the side-by-side comparison to showcase the before-and-after memory difference on a single screen.

---

## 12. Example: Structured Review Output

```json
{
  "summary": "Identified critical SQL injection vulnerability due to unsafe string concatenation with user input.",
  "risk": "critical",
  "issues": [
    {
      "severity": "critical",
      "line": "Line 5",
      "title": "SQL Injection via String Concatenation",
      "why": "[Team Memory Standard Violation]: Violates team standard requiring parameterized queries or approved ORM. Direct concatenation allows arbitrary SQL injection.",
      "suggestion": "cursor.execute('SELECT id, username, email, role FROM users WHERE id = %s', (user_id,))"
    }
  ],
  "team_rules_used": [
    "Never construct SQL queries using string concatenation or f-strings with user input. Always use parameterized queries or the approved team ORM."
  ],
  "learning": [
    "Always enforce parameterized queries across all database drivers and avoid dynamic SQL assembly."
  ]
}
```

---

## 13. Future Improvements

- **GitHub PR Sidecar Integration**: Automatically post Hindsight-grounded reviews on pull requests.
- **Repository-Level Memory Scopes**: Support sub-banks per microservice or repository alongside team-wide banks.
- **Developer Feedback Loop**: Allow developers to thumbs-up/down retained lessons to refine memory quality over time.
- **IDE Extensions**: Lightweight extension for VS Code / JetBrains to query team memory directly while typing code.
