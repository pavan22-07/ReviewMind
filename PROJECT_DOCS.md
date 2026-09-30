# ReviewMind — Complete Project Documentation

> **Version:** MVP 1.0  
> **Repository:** https://github.com/pavan22-07/ReviewMind.git  
> **Hackathon Track:** Code Review Agent with Hindsight Persistent Organizational Memory  
> **Tagline:** *"A Code Review Agent that learns how your team reviews code."*

---

## 1. Problem Statement

Every software engineering team develops a unique body of institutional knowledge over time:

- **Coding standards** (e.g., always use parameterized queries, never expose raw exceptions in API responses)
- **Recurring mistakes** (e.g., business logic leaking into controllers, missing input validation)
- **Architectural preferences** (e.g., strict service-layer separation, domain-driven layering)
- **Review culture** (e.g., specific patterns that have caused incidents, conventions from post-mortems)

**Generic AI code reviewers are stateless.** They treat every pull request as a blank slate and produce generic, industry-wide advice that ignores team-specific context. They cannot:
- Recall that your team enforces parameterized queries specifically (not just "avoid SQL injection")
- Know that your team previously decided to reject raw exception exposure in API responses
- Apply architectural rules specific to your codebase's layering decisions
- Accumulate knowledge from past reviews and apply it to future ones

**ReviewMind solves this** by integrating **Hindsight**, a persistent semantic memory service, to give the code review agent a continuously growing organisational brain that recalls and applies accumulated team knowledge during every review.

---

## 2. How ReviewMind Works — The Core Loop

```
Developer submits code snippet
         │
         ▼
  [Step 1: Recall]
  ReviewMind queries Hindsight semantic memory bank
  with a query derived from the code's language/patterns
  (e.g. "python team standards for sql queries and parameterized statements")
         │
         ▼
  Hindsight returns relevant team memories
  (e.g. seeded rules + previously learned lessons from past reviews)
         │
         ▼
  [Step 2: Ground]
  Retrieved memories are injected into the LLM system prompt
  alongside the source code — Groq LLM (openai/gpt-oss-120b)
  performs a grounded review referencing both general best practices
  AND team-specific memory
         │
         ▼
  [Step 3: Structured Output]
  LLM responds with structured JSON:
  { summary, risk, issues[], team_rules_used[], learning[] }
         │
         ▼
  [Step 4: Retain]
  ReviewMind extracts newly synthesized lessons from `learning[]`
  and retains them back into Hindsight for future reviews
  — the memory bank grows with every review session
```

---

## 3. Tech Stack

| Layer | Technology | Role |
|-------|-----------|------|
| **Frontend UI** | [Streamlit](https://streamlit.io/) 1.x | Web dashboard; dark-themed, premium AI SaaS aesthetic |
| **LLM Inference** | [Groq API](https://groq.com/) — `openai/gpt-oss-120b` | Ultra-fast LLM inference for structured code review |
| **Persistent Memory** | [Hindsight](https://vectorize.io/hindsight/) — `hindsight-client` SDK | Semantic memory bank: recall + retain operations |
| **Data Models** | [Pydantic](https://docs.pydantic.dev/) v2 | Typed schemas for review results, issues, memory items |
| **Configuration** | `python-dotenv` | Environment variable loading from `.env` |
| **Language** | Python 3.13 | Backend logic, SDK integration, agent orchestration |

---

## 4. Project File Structure

```
ReviewMind/
│
├── app.py                     # Streamlit frontend dashboard (presentation layer only)
├── demo_samples.py            # Pre-built vulnerable code demo scenarios
├── requirements.txt           # Python dependencies
├── .env                       # API keys (GROQ_API_KEY, HINDSIGHT_API_KEY, etc.)
├── .env.example               # Template for required environment variables
├── .gitignore
│
├── src/
│   ├── __init__.py
│   ├── config.py              # Settings dataclass, env variable loading, update_settings()
│   ├── models.py              # Pydantic data models: ReviewIssue, ReviewResult, MemoryItem
│   ├── memory.py              # HindsightMemoryManager: recall, retain, ensure_bank, seed
│   ├── reviewer.py            # CodeReviewer: orchestrates recall→LLM→parse→retain pipeline
│   └── prompts.py             # SYSTEM_PROMPT + build_review_user_prompt() function
│
├── test_app.py                # Unit/smoke tests for imports, models, config, parsing
├── test_memory_flow.py        # Full lifecycle mock test: recall→review→retain cycle
└── verify_hindsight_live.py   # Live integration test against real Hindsight + Groq APIs
```

---

## 5. Data Models (src/models.py)

### `ReviewIssue`
Represents a single code issue identified in a review.

| Field | Type | Description |
|-------|------|-------------|
| `severity` | `Literal["critical","high","medium","low"]` | Severity classification |
| `line` | `str` | Line number or range (e.g. "Line 4", "Lines 10-15") |
| `title` | `str` | Concise issue title |
| `why` | `str` | Detailed explanation including team-memory vs. general best practice distinction |
| `suggestion` | `str` | Actionable fix with concrete code snippet |

### `ReviewResult`
The complete output of a ReviewMind review session.

| Field | Type | Description |
|-------|------|-------------|
| `summary` | `str` | Executive summary of overall code quality |
| `risk` | `Literal["critical","high","medium","low"]` | Overall risk rating |
| `issues` | `List[ReviewIssue]` | All identified issues |
| `team_rules_used` | `List[str]` | Team memory rules from Hindsight that were applied |
| `learning` | `List[str]` | New reusable lessons synthesized for retention into Hindsight |
| `used_memory` | `bool` | Whether Hindsight memory was active for this review |
| `recalled_memories` | `List[str]` | Raw memory texts recalled from Hindsight and injected into prompt |
| `language` | `str` | Programming language of reviewed code |
| `model` | `str` | Groq model used |
| `retention_status` | `List[str]` | Confirmation messages from Hindsight for retained lessons |

### `MemoryItem`
A single unit of team memory recalled from or retained into Hindsight.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique memory unit ID (from Hindsight) |
| `text` | `str` | The actual memory text / rule statement |
| `category` | `str` | `team_standard`, `common_mistake`, `architectural_preference`, or `review_lesson` |
| `tags` | `List[str]` | Semantic tags for filtering |
| `context` | `Optional[str]` | Additional context or rationale |
| `metadata` | `Dict` | Key-value metadata (language, source, timestamp) |
| `score` | `Optional[float]` | Semantic similarity score from Hindsight retrieval |

---

## 6. Configuration (src/config.py)

All configuration is loaded from environment variables (`.env` file in the project root).

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `GROQ_API_KEY` | — (required) | Groq cloud API key |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Groq model identifier |
| `HINDSIGHT_API_KEY` | — (required) | Hindsight cloud API key |
| `HINDSIGHT_API_URL` | `https://api.hindsight.vectorize.io` | Hindsight base URL |
| `HINDSIGHT_BANK_ID` | `reviewmind-team` | Team memory bank name |

The `Settings` dataclass provides `is_groq_ready()`, `is_hindsight_ready()`, and `validate()` helpers used by the UI to show service health status in the sidebar.

---

## 7. Hindsight Memory Layer (src/memory.py)

`HindsightMemoryManager` wraps the official `hindsight-client` Python SDK.

### Key Methods

#### `ensure_bank_exists(bank_id)`
- Calls `client.create_bank(bank_id, retain_mission, reflect_mission)` to provision or verify the team memory bank.
- Idempotent: handles HTTP 409 Conflict (bank already exists) gracefully.
- Registers verified banks in `self._verified_banks` set to avoid redundant API calls.

#### `recall_memories(query, bank_id, budget, max_tokens)`
- Converts a semantic query string into a Hindsight `client.recall()` call.
- Guaranteed safe: before calling `recall()`, checks `_verified_banks` and calls `ensure_bank_exists()` if needed.
- Auto-heals on HTTP 404 (bank doesn't exist): provisions bank and retries recall.
- Returns `List[MemoryItem]` and an optional error string.

#### `retain_knowledge(content, category, language, source, tags, metadata, bank_id)`
- Stores a new lesson or rule into the Hindsight bank via `client.retain()`.
- Pre-flight bank verification before `retain()` (same pattern as recall).
- Auto-heals on HTTP 404 with one retry.
- Returns `(success: bool, message: str)`.

#### `seed_default_standards(bank_id)`
- Seeds 4 foundational engineering rules into the bank at startup (idempotent).
- These are reusable team-agnostic examples to pre-populate the bank for hackathon demos:
  1. SQL injection prevention via parameterized queries
  2. Error/exception exposure prevention in API responses
  3. Layered architecture enforcement (no business logic in controllers)
  4. Input validation at all public API endpoints

#### `test_connection(bank_id)`
- End-to-end ping: ensures bank exists, then performs a low-budget recall query.
- Returns `(ok: bool, message: str)` for the sidebar "Ping Test" button.

### Error Handling
Both `ApiException` (from `hindsight_client_api`) and `ClientResponseError` (from `aiohttp`) are caught uniformly. HTTP status code is extracted via `getattr(e, "status", None)` to normalize across exception types.

---

## 8. Code Reviewer Agent (src/reviewer.py)

`CodeReviewer` orchestrates the complete review lifecycle.

### `review(code, language, use_memory, auto_retain, custom_recall_query)`

**Step 1 — Validation**
- Checks for empty code input.
- Checks max code character limit (25,000 chars).
- Checks Groq API key presence.

**Step 2 — Semantic Recall Query Generation**
- `generate_recall_query(code, language)` scans code for signal keywords (SQL, exception handling, validation, authentication, route handlers) and builds a targeted Hindsight query string.

**Step 3 — Hindsight Recall**
- Calls `memory_manager.recall_memories(query, budget="mid")`.
- Extracts raw `text` from `MemoryItem` objects for injection into LLM prompt.

**Step 4 — Prompt Construction**
- Calls `build_review_user_prompt(code, language, recalled_memories)` from `prompts.py`.
- Injects code + team memory context as a structured user turn.

**Step 5 — Groq LLM Inference**
- First attempt: `response_format={"type": "json_object"}` for strict JSON enforcement.
- Fallback: retries without response format if the model doesn't support it.

**Step 6 — JSON Parsing**
- `_parse_json_response()` strips markdown code fences, parses JSON, validates against `ReviewResult` schema.
- Graceful fallback: if JSON is invalid, returns a structured error result rather than crashing.

**Step 7 — Learning Retention**
- If `auto_retain=True` and `learning` array is non-empty, each lesson is retained into Hindsight via `memory_manager.retain_knowledge()`.

---

## 9. LLM Prompt Design (src/prompts.py)

### System Prompt
The system prompt instructs ReviewMind to:
1. **Distinguish** between `[Team Memory Standard]` and `[General Best Practice]` in every finding.
2. **Never fabricate** team rules — only cite rules present in the `RECALLED TEAM MEMORY` section.
3. **Synthesize 1–3 reusable lessons** in the `learning` array (formulated as general engineering principles, not snippet-specific).
4. **Review across 8 dimensions**: Correctness, Security, Bugs/Edge Cases, Maintainability, Performance, Error Handling, Architecture, Team Standards.
5. **Output strict JSON only** — no markdown wrappers, no prose before/after.

### User Prompt
`build_review_user_prompt(code, language, recalled_memories)` generates:
```
RECALLED TEAM MEMORY (from Hindsight):
[RULE-1]: <memory text>
[RULE-2]: <memory text>
...

SOURCE CODE (Language: python):
<code>

Please review the above code...
```

The `[RULE-N]` indexing allows the LLM to reference rules by number, and the `resolve_team_rule_text()` function in `app.py` reverse-maps those references back to the actual memory text for display.

---

## 10. Frontend UI (app.py)

Built with **Streamlit** as a single-page application with a sidebar navigation model.

### Pages / Views

| Nav Option | Description |
|-----------|-------------|
| `🔍 Code Review` | Primary view: code input (left) + review output (right). Run review, see findings, see recalled memory rules applied. |
| `🧠 Team Memory` | Browse and query the Hindsight bank directly. View all recalled memories with scores. Manage bank seeding. |
| `📊 Analytics` | Session-level statistics: total reviews, severity breakdowns, memory utilization rate, lessons retained. |
| `🧪 Interactive Demo` | Side-by-side comparison: generic review (no memory) vs. Hindsight-grounded review (with memory). Best for demo. |

### Theme
- Global background: `#090514` (near-black purple-tinted)
- Accent: `#D946EF` / `#E879F9` (magenta/pink glow)
- Card background: `#120C24` / `#160F2E`
- Text: `#F8FAFC` (primary), `#94A3B8` (muted), `#CBD5E1` (secondary)
- Dark is enforced via CSS overrides on Streamlit's internal DOM structure.

---

## 11. Demo Scenarios (demo_samples.py)

Four pre-built vulnerable code snippets covering the four most common team-memory-testable findings:

| ID | Title | Vulnerability Demonstrated |
|----|-------|---------------------------|
| `sql_injection` | SQL Injection (String Concatenation in Query) | Hindsight rule: parameterized queries |
| `raw_exception` | Raw Exception Exposure (Information Disclosure) | Hindsight rule: never expose exceptions in API responses |
| `missing_validation` | Missing Input Validation (Business Logic Vulnerability) | Hindsight rule: validate all inputs at controller boundaries |
| `controller_business_logic` | Business Logic in Controller (Architectural Violation) | Hindsight rule: strict layered architecture |

Each sample includes:
- `vulnerable_code`: the bad version submitted for review
- `fixed_code`: the correct version (shown for reference in demos)
- `expected_team_rule`: the Hindsight rule that should fire
- `description`: scenario context
- `language`: programming language

---

## 12. Tests

### `test_app.py` — Unit and Smoke Tests
7 test suites run without live API calls:
1. Module imports
2. Config loading and credential reporting
3. Pydantic model instantiation and field validation
4. Demo sample structure and content
5. Prompt generation with and without memory injection
6. Resilient JSON parser (valid, invalid, empty inputs)
7. Missing credentials graceful handling (no crashes)

### `test_memory_flow.py` — Mocked Full Lifecycle Test
End-to-end flow using `MagicMock` Hindsight and Groq clients:
1. Phase 1: Mock recall → assert correct MemoryItem returned
2. Phase 2: Mock Groq response → assert structured review parsed correctly
3. Phase 3: Assert Hindsight `retain()` was called with synthesized lesson

### `verify_hindsight_live.py` — Live Integration Verification
Tests against real Hindsight Cloud API and real Groq API:
1. Bank provisioning / connection test
2. Seeding foundational standards
3. Real recall (asserts at least 1 memory returned)
4. Real retain (stores a new architectural rule)
5. Full live review with Groq LLM + Hindsight grounding
6. Checks no 404 errors appear in execution logs

---

## 13. Environment Setup

```bash
# Clone repository
git clone https://github.com/pavan22-07/ReviewMind.git
cd ReviewMind

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and fill in:
# GROQ_API_KEY=gsk_...
# HINDSIGHT_API_KEY=hs_...
# HINDSIGHT_BANK_ID=reviewmind-team

# Run tests
python test_app.py
python test_memory_flow.py

# Start application
streamlit run app.py
```

**Requirements (requirements.txt):**
```
streamlit>=1.28.0
groq>=0.11.0
hindsight-client>=0.5.0
pydantic>=2.0.0
python-dotenv>=1.0.0
aiohttp>=3.9.0
```

---

## 14. Architecture Diagram

```
╔══════════════════════════════════════════════════════════════════════╗
║                     REVIEWMIND SYSTEM ARCHITECTURE                   ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║   Developer / Code Reviewer                                           ║
║         │                                                             ║
║         │  (pastes code snippet + selects language)                  ║
║         ▼                                                             ║
║   ┌─────────────────────────────────────────┐                        ║
║   │        Streamlit Dashboard (app.py)      │  Dark-themed AI UI    ║
║   │   Code Input │ Review Output │ Nav       │                       ║
║   └───────────────────┬─────────────────────┘                        ║
║                       │                                               ║
║                       ▼                                               ║
║   ┌──────────────────────────────────────────────────────────┐        ║
║   │               CodeReviewer (src/reviewer.py)              │        ║
║   │  1. generate_recall_query(code, language)                 │        ║
║   │  2. memory_manager.recall_memories(query)  ──────────────┼──┐    ║
║   │  3. build_review_user_prompt(code, memories)              │  │    ║
║   │  4. groq_client.chat.completions.create(...)              │  │    ║
║   │  5. _parse_json_response(raw_llm_output)                  │  │    ║
║   │  6. memory_manager.retain_knowledge(lessons)  ────────────┼──┤    ║
║   └──────────────────────────────────────────────────────────┘  │    ║
║                                                                   │    ║
║         ┌─────────────────────────────────────────────────────┐  │    ║
║         │              External APIs                           │  │    ║
║         │                                                      │  │    ║
║         │  ┌──────────────────────┐  ┌─────────────────────┐ │  │    ║
║         │  │  Hindsight Cloud     │  │   Groq Cloud        │ │  │    ║
║         │  │  (vectorize.io)      │  │   (groq.com)        │ │  │    ║
║         │  │  /v1/banks/          │  │   chat completions  │ │  │    ║
║         │  │  - recall()          │◄─┤   openai/gpt-oss-   │ │  │    ║
║         │  │  - retain()          │  │   120b              │ │  │    ║
║         │  │  - create_bank()     │  └─────────────────────┘ │  │    ║
║         │  └──────────────────────┘                          │  │    ║
║         └─────────────────────────────────────────────────────┘  │    ║
║                              │                                    │    ║
║         ┌────────────────────┴──────────────────────────────────┐│    ║
║         │  HindsightMemoryManager (src/memory.py)               ││    ║
║         │  - ensure_bank_exists()    ← called before every op   ││    ║
║         │  - _verified_banks: set    ← cache of known banks     ││    ║
║         │  - 404 auto-heal + retry   ← resilient to cold start  ││    ║
║         └───────────────────────────────────────────────────────┘│    ║
║                                                                   │    ║
╚═══════════════════════════════════════════════════════════════════╧════╝
```

---

## 15. Key Design Decisions

### Why Hindsight?
Hindsight provides a semantic memory bank with:
- **Persistent storage**: memory survives across sessions and deployments
- **Semantic recall**: retrieval by meaning, not just keyword match
- **Structured metadata**: tags, categories, timestamps on each memory unit
- **Retain**: new lessons are stored in natural language, not structured schemas

### Why Groq?
- Extremely low inference latency (essential for interactive code review demos)
- Supports `response_format: json_object` for strict structured output
- `openai/gpt-oss-120b` provides high reasoning quality for code analysis

### Why the Learning Loop Matters
Without retention, every review session starts cold. With retention:
- Session 1: ReviewMind reviews SQL injection code, learns "always use parameterized queries"
- Session 5: ReviewMind reviews a new module — recalls the parameterized query rule from memory *and* any variations it synthesized in sessions 2–4
- Over time: the agent's reviews become more team-specific, more consistent, and more aligned with what the team actually cares about

### Resilient Bank Initialization
The `ensure_bank_exists()` method is called proactively before every `recall()` and `retain()` to guarantee the Hindsight bank exists. This eliminates the HTTP 404 race condition that occurs when an agent tries to read from a bank that hasn't been provisioned yet.

---

## 16. Future Roadmap (Post-Hackathon)

- **PR integration**: GitHub/GitLab webhook listener to auto-review pull requests
- **Multi-bank support**: Different Hindsight banks per project or team
- **Admin UI**: Bank health dashboard, memory browsing, rule management
- **Feedback loop**: Developers can upvote/downvote recalled rules to improve relevance over time
- **CI/CD integration**: CLI mode for automated review in pipelines
- **Multi-language code intelligence**: Deeper AST parsing per language for richer query generation
