"""
Core ReviewMind Code Review Agent.
Orchestrates Hindsight memory recall, Groq LLM inference, structured output parsing,
and the continuous learning retention loop.
"""

import json
import re
import logging
from typing import Optional, List, Tuple
from datetime import datetime

import groq
from groq import Groq

from src.config import Settings, get_settings
from src.models import ReviewResult, ReviewIssue
from src.memory import HindsightMemoryManager
from src.prompts import SYSTEM_PROMPT, build_review_user_prompt

logger = logging.getLogger("reviewmind.reviewer")


class CodeReviewer:
    """
    ReviewMind code review agent.
    Performs memory-augmented code reviews by recalling organizational memory
    from Hindsight, executing LLM analysis via Groq, and retaining new lessons.
    """

    def __init__(
        self,
        config: Optional[Settings] = None,
        memory_manager: Optional[HindsightMemoryManager] = None,
    ):
        self.config = config or get_settings()
        self.memory_manager = memory_manager or HindsightMemoryManager(self.config)
        self._groq_client: Optional[Groq] = None
        self._initialize_groq()

    def _initialize_groq(self) -> None:
        """Initialize or refresh the Groq client."""
        if self.config.groq_api_key:
            try:
                self._groq_client = Groq(api_key=self.config.groq_api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self._groq_client = None
        else:
            self._groq_client = None

    def refresh_clients(self) -> None:
        """Refresh Groq and Hindsight clients after config updates."""
        self._initialize_groq()
        self.memory_manager.refresh_client()

    def generate_recall_query(self, code: str, language: str) -> str:
        """
        Derive a focused semantic query for Hindsight based on code patterns and language.
        Extracts key security, architecture, or library concepts.
        """
        code_lower = code.lower()
        signals = []

        if any(k in code_lower for k in ["select", "insert", "update", "delete", "where", "cursor", "query", "sql"]):
            signals.append("sql database queries and parameterized statements")
        if any(k in code_lower for k in ["except", "catch", "traceback", "error", "throw", "raise"]):
            signals.append("exception handling and error disclosure")
        if any(k in code_lower for k in ["route", "controller", "view", "endpoint", "request.args", "request.get_json"]):
            signals.append("controller route handlers and service layer architecture")
        if any(k in code_lower for k in ["validate", "validation", "amount", "input", "sanitize", "transfer"]):
            signals.append("input validation and data integrity")
        if any(k in code_lower for k in ["token", "password", "secret", "auth", "jwt"]):
            signals.append("authentication security and secret management")

        if signals:
            return f"{language} team coding standards for " + ", ".join(signals)
        return f"{language} team coding standards, security rules, and architectural conventions"

    def review(
        self,
        code: str,
        language: str = "python",
        use_memory: bool = True,
        auto_retain: bool = True,
        custom_recall_query: Optional[str] = None,
    ) -> Tuple[ReviewResult, List[str]]:
        """
        Execute the complete review flow:
        1. Recall relevant team memory from Hindsight (if enabled)
        2. Prompt the Groq LLM with code + memory context
        3. Parse structured JSON review findings
        4. Retain extracted lessons back into Hindsight

        Returns:
            Tuple of (ReviewResult, list of execution logs/status messages)
        """
        logs: List[str] = []

        # 1. Validation checks
        stripped_code = code.strip()
        if not stripped_code:
            return (
                ReviewResult(
                    summary="No source code was submitted for review.",
                    risk="low",
                    issues=[],
                    team_rules_used=[],
                    learning=[],
                    used_memory=use_memory,
                    language=language,
                    model=self.config.groq_model,
                ),
                ["Validation error: Source code input was empty."],
            )

        if len(stripped_code) > self.config.max_code_chars:
            return (
                ReviewResult(
                    summary=f"Submitted code exceeds maximum limit of {self.config.max_code_chars} characters.",
                    risk="medium",
                    issues=[
                        ReviewIssue(
                            severity="medium",
                            line="N/A",
                            title="Code Input Too Large",
                            why="For optimal LLM analysis and memory indexing, please submit modular snippets or single functions.",
                            suggestion="Split your code into individual components or functions before reviewing.",
                        )
                    ],
                    team_rules_used=[],
                    learning=[],
                    used_memory=use_memory,
                    language=language,
                    model=self.config.groq_model,
                ),
                ["Validation warning: Code length exceeded safety limit."],
            )

        # Check Groq API Key
        if not self.config.groq_api_key or not self._groq_client:
            missing_msg = (
                "GROQ_API_KEY is not configured. Please supply a valid Groq API key "
                "in your `.env` file or enter it in the sidebar settings."
            )
            return (
                ReviewResult(
                    summary="Review could not be completed: Missing Groq API Key.",
                    risk="low",
                    issues=[
                        ReviewIssue(
                            severity="high",
                            line="Configuration",
                            title="Missing GROQ_API_KEY",
                            why="The ReviewMind agent requires a Groq API key to power its LLM review inference.",
                            suggestion="Add `GROQ_API_KEY=gsk_...` to your `.env` file or paste it in the application sidebar.",
                        )
                    ],
                    team_rules_used=[],
                    learning=[],
                    used_memory=use_memory,
                    language=language,
                    model=self.config.groq_model,
                ),
                [missing_msg],
            )

        # 2. Recall relevant memory from Hindsight
        recalled_memories: List[str] = []
        if use_memory:
            recall_query = custom_recall_query or self.generate_recall_query(stripped_code, language)
            logs.append(f"🧠 Querying Hindsight memory bank '{self.config.hindsight_bank_id}' with: '{recall_query}'")

            if self.memory_manager.is_available():
                mem_items, err = self.memory_manager.recall_memories(
                    query=recall_query,
                    budget=self.config.default_recall_budget,
                )
                if err:
                    logs.append(f"⚠️ Hindsight Recall Note: {err}")
                elif mem_items:
                    recalled_memories = [m.text for m in mem_items]
                    logs.append(f"✅ Recalled {len(recalled_memories)} team memory facts from Hindsight.")
                else:
                    logs.append("ℹ️ Hindsight connected, but no matching memories found in bank.")
            else:
                logs.append("⚠️ Hindsight API key not set. Proceeding without team memory.")
        else:
            logs.append("⚡ Running in GENERIC mode (Team memory disabled).")

        # 3. Construct Prompts
        user_prompt = build_review_user_prompt(
            code=stripped_code,
            language=language,
            recalled_memories=recalled_memories,
        )

        # 4. Invoke Groq LLM
        model_name = self.config.groq_model
        logs.append(f"🤖 Invoking Groq LLM ({model_name})...")

        raw_content = ""
        try:
            # First attempt with JSON object response format
            try:
                chat_completion = self._groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    model=model_name,
                    response_format={"type": "json_object"},
                    temperature=0.2,
                )
            except Exception as format_exc:
                logger.info(f"Retrying without explicit json_object format: {format_exc}")
                chat_completion = self._groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    model=model_name,
                    temperature=0.2,
                )

            raw_content = chat_completion.choices[0].message.content or ""
            logs.append("✅ Received response from Groq LLM.")

        except groq.AuthenticationError as e:
            logs.append(f"❌ Groq Authentication Error: {str(e)}")
            return (
                ReviewResult(
                    summary="Groq authentication failed. Please verify your GROQ_API_KEY.",
                    risk="low",
                    issues=[
                        ReviewIssue(
                            severity="high",
                            line="Configuration",
                            title="Invalid Groq API Key",
                            why=str(e),
                            suggestion="Check your Groq API key in .env or the UI sidebar.",
                        )
                    ],
                    team_rules_used=[],
                    learning=[],
                    used_memory=use_memory,
                    language=language,
                    model=model_name,
                ),
                logs,
            )
        except groq.RateLimitError as e:
            logs.append(f"❌ Groq Rate Limit Exceeded: {str(e)}")
            return (
                ReviewResult(
                    summary="Groq rate limit exceeded. Please wait a moment before reviewing again.",
                    risk="low",
                    issues=[
                        ReviewIssue(
                            severity="medium",
                            line="API",
                            title="Rate Limit Exceeded",
                            why=str(e),
                            suggestion="Wait a few seconds or try switching to another Groq model.",
                        )
                    ],
                    team_rules_used=[],
                    learning=[],
                    used_memory=use_memory,
                    language=language,
                    model=model_name,
                ),
                logs,
            )
        except Exception as e:
            logs.append(f"❌ Groq API Failure: {str(e)}")
            return (
                ReviewResult(
                    summary=f"Groq API error encountered: {str(e)}",
                    risk="low",
                    issues=[
                        ReviewIssue(
                            severity="high",
                            line="API",
                            title="Groq API Error",
                            why=str(e),
                            suggestion="Verify your internet connection and Groq service status.",
                        )
                    ],
                    team_rules_used=[],
                    learning=[],
                    used_memory=use_memory,
                    language=language,
                    model=model_name,
                ),
                logs,
            )

        # 5. Parse Structured Output with robust fallback
        parsed_result = self._parse_json_response(
            raw_content=raw_content,
            language=language,
            model_name=model_name,
            used_memory=use_memory,
            recalled_memories=recalled_memories,
            logs=logs,
        )

        # 6. Learning Loop: Retain extracted lessons into Hindsight
        retention_statuses: List[str] = []
        if auto_retain and use_memory and parsed_result.learning and self.memory_manager.is_available():
            logs.append(f"📝 Extracting {len(parsed_result.learning)} reusable lessons to retain in Hindsight...")
            for lesson in parsed_result.learning:
                success, status_msg = self.memory_manager.retain_knowledge(
                    content=lesson,
                    category="review_lesson",
                    language=language,
                    source="code_review",
                    tags=[language, "learned-lesson", "reviewmind"],
                )
                retention_statuses.append(status_msg)
                logs.append(f"  • {status_msg}")

        parsed_result.retention_status = retention_statuses
        return parsed_result, logs

    def _parse_json_response(
        self,
        raw_content: str,
        language: str,
        model_name: str,
        used_memory: bool,
        recalled_memories: List[str],
        logs: List[str],
    ) -> ReviewResult:
        """
        Safely parse the LLM's response into a ReviewResult model.
        Includes sanitization and graceful fallback if JSON parsing errors occur.
        """
        cleaned = raw_content.strip()

        # Remove markdown code block if present
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # Regex search for JSON object if surrounded by extra text
        json_match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if json_match:
            cleaned = json_match.group(1)

        try:
            data = json.loads(cleaned)
            summary = data.get("summary", "Code review completed successfully.")
            risk = data.get("risk", "medium").lower()
            if risk not in ["critical", "high", "medium", "low"]:
                risk = "medium"

            raw_issues = data.get("issues", [])
            issues: List[ReviewIssue] = []
            for issue_dict in raw_issues:
                if isinstance(issue_dict, dict):
                    sev = issue_dict.get("severity", "medium").lower()
                    if sev not in ["critical", "high", "medium", "low"]:
                        sev = "medium"
                    issues.append(
                        ReviewIssue(
                            severity=sev,
                            line=str(issue_dict.get("line", "General")),
                            title=str(issue_dict.get("title", "Review Finding")),
                            why=str(issue_dict.get("why", "")),
                            suggestion=str(issue_dict.get("suggestion", "")),
                        )
                    )

            team_rules_used = [str(r) for r in data.get("team_rules_used", []) if r]
            learning = [str(l) for l in data.get("learning", []) if l]

            return ReviewResult(
                summary=summary,
                risk=risk,
                issues=issues,
                team_rules_used=team_rules_used,
                learning=learning,
                used_memory=used_memory,
                recalled_memories=recalled_memories,
                language=language,
                model=model_name,
            )

        except Exception as e:
            logger.warning(f"Failed to parse JSON response: {e}. Raw content: {raw_content[:200]}")
            logs.append("⚠️ LLM output was not strictly parseable JSON. Using resilient fallback.")

            # Resilient fallback: present the raw response in a clean ReviewResult
            return ReviewResult(
                summary="Review completed. (Formatted with resilient fallback parser)",
                risk="medium",
                issues=[
                    ReviewIssue(
                        severity="medium",
                        line="General",
                        title="LLM Review Findings",
                        why=raw_content[:1500] if raw_content else "No output returned.",
                        suggestion="Please inspect findings above or re-run review.",
                    )
                ],
                team_rules_used=[],
                learning=[],
                used_memory=used_memory,
                recalled_memories=recalled_memories,
                language=language,
                model=model_name,
            )
