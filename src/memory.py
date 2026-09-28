"""
Hindsight memory management layer for ReviewMind.
Implements the persistent organizational memory layer using the official hindsight-client SDK.
"""

import logging
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime

from hindsight_client import Hindsight
from hindsight_client_api.exceptions import ApiException
from aiohttp import ClientResponseError

from src.config import Settings, get_settings
from src.models import MemoryItem

logger = logging.getLogger("reviewmind.memory")


class HindsightMemoryManager:
    """
    Manages persistent organizational memory for code review teams using Hindsight.

    Provides high-level methods to:
    - Initialize and ensure team memory banks
    - Recall relevant team rules, recurring mistakes, and architectural preferences
    - Retain useful lessons learned from code reviews with rich metadata
    - Seed foundational team engineering standards
    """

    def __init__(self, config: Optional[Settings] = None):
        self.config = config or get_settings()
        self._verified_banks: set[str] = set()
        self._client: Optional[Hindsight] = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the Hindsight client using current configuration."""
        base_url = self.config.hindsight_api_url or "https://api.hindsight.vectorize.io"
        api_key = self.config.hindsight_api_key or None
        self._verified_banks = set()

        try:
            self._client = Hindsight(
                base_url=base_url,
                api_key=api_key,
                user_agent="ReviewMind-Agent/1.0",
                timeout=15.0,
            )
        except Exception as e:
            logger.error(f"Failed to instantiate Hindsight client: {e}")
            self._client = None

    def refresh_client(self) -> None:
        """Re-initialize client after configuration changes."""
        self._initialize_client()

    def is_available(self) -> bool:
        """Check if Hindsight credentials are configured."""
        return bool(self.config.hindsight_api_key and self._client)

    def ensure_bank_exists(self, bank_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Ensure the designated memory bank exists in Hindsight.
        Creates or updates it with a mission tailored for engineering code review memory.
        """
        if not self.is_available():
            return False, "HINDSIGHT_API_KEY is not configured. Please provide an API key in .env or the UI."

        target_bank = (bank_id or self.config.hindsight_bank_id).strip()
        if not target_bank:
            return False, "HINDSIGHT_BANK_ID cannot be empty."

        mission_text = (
            "Organizational memory bank for engineering team code review knowledge. "
            "Stores team coding standards, recurring mistakes, architectural conventions, "
            "security rules, and lessons learned from past code reviews."
        )

        try:
            # Use high-level create_bank method which creates or updates the bank
            self._client.create_bank(
                bank_id=target_bank,
                retain_mission=mission_text,
                reflect_mission=mission_text,
            )
            self._verified_banks.add(target_bank)
            return True, f"Memory bank '{target_bank}' is ready and configured."
        except (ApiException, ClientResponseError) as e:
            status = getattr(e, "status", None)
            body = getattr(e, "body", None) or getattr(e, "message", None) or str(e)
            if status == 409:
                self._verified_banks.add(target_bank)
                return True, f"Memory bank '{target_bank}' is ready and verified."
            logger.error(f"Hindsight API Error during create_bank ({status}): {body}")
            if status == 401:
                return False, "Authentication failed: Invalid Hindsight API Key."
            return False, f"Hindsight API Error ({status}): {body}"
        except Exception as e:
            logger.exception("Unexpected error while ensuring Hindsight bank exists")
            return False, f"Connection error: {str(e)}"

    def recall_memories(
        self,
        query: str,
        bank_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        budget: str = "mid",
        max_tokens: int = 4096,
    ) -> Tuple[List[MemoryItem], Optional[str]]:
        """
        Recall relevant team knowledge from Hindsight using semantic search.
        Guarantees that the target bank exists before issuing the recall request.

        Args:
            query: Semantic search query describing code constructs, language, or domain
            bank_id: Target memory bank ID (defaults to config)
            tags: Optional tags to filter results
            budget: Recall budget level ('low', 'mid', 'high')
            max_tokens: Token budget for recalled facts

        Returns:
            Tuple of (list of MemoryItem, error message if any)
        """
        if not self.is_available():
            return [], "HINDSIGHT_API_KEY not configured. Memory recall is disabled."

        target_bank = (bank_id or self.config.hindsight_bank_id).strip()
        if not target_bank:
            return [], "HINDSIGHT_BANK_ID cannot be empty."

        # Proactively ensure the bank exists in Hindsight before issuing recall
        if target_bank not in self._verified_banks:
            ok, bank_msg = self.ensure_bank_exists(target_bank)
            if not ok:
                logger.warning(f"Could not proactively ensure bank '{target_bank}' before recall: {bank_msg}")

        try:
            # Official Hindsight recall method
            response = self._client.recall(
                bank_id=target_bank,
                query=query,
                tags=tags,
                budget=budget,
                max_tokens=max_tokens,
            )

            memories: List[MemoryItem] = []
            if response and hasattr(response, "results") and response.results:
                for item in response.results:
                    # Extract score if available
                    score = None
                    if hasattr(item, "scores") and item.scores:
                        score = getattr(item.scores, "final", None) or getattr(
                            item.scores, "semantic", None
                        )

                    metadata = getattr(item, "metadata", {}) or {}
                    category = metadata.get("category", "team_standard") if isinstance(metadata, dict) else "team_standard"

                    memories.append(
                        MemoryItem(
                            id=getattr(item, "id", "") or "",
                            text=getattr(item, "text", ""),
                            category=category,
                            tags=getattr(item, "tags", []) or [],
                            context=getattr(item, "context", None),
                            metadata=metadata if isinstance(metadata, dict) else {},
                            score=float(score) if score is not None else None,
                        )
                    )

            return memories, None

        except (ApiException, ClientResponseError) as e:
            status = getattr(e, "status", None)
            body = getattr(e, "body", None) or getattr(e, "message", None) or str(e)
            logger.error(f"Hindsight API error during recall ({status}): {body}")
            if status == 401:
                return [], "Hindsight Authentication Error: Invalid API Key."
            if status == 404:
                # Bank was missing or not yet indexed; auto-heal by creating and retrying
                logger.info(f"Bank '{target_bank}' not found (404); attempting auto-creation and retry...")
                created_ok, _ = self.ensure_bank_exists(target_bank)
                if created_ok:
                    try:
                        retry_resp = self._client.recall(
                            bank_id=target_bank,
                            query=query,
                            tags=tags,
                            budget=budget,
                            max_tokens=max_tokens,
                        )
                        retry_memories: List[MemoryItem] = []
                        if retry_resp and hasattr(retry_resp, "results") and retry_resp.results:
                            for item in retry_resp.results:
                                score = None
                                if hasattr(item, "scores") and item.scores:
                                    score = getattr(item.scores, "final", None) or getattr(
                                        item.scores, "semantic", None
                                    )
                                metadata = getattr(item, "metadata", {}) or {}
                                category = metadata.get("category", "team_standard") if isinstance(metadata, dict) else "team_standard"
                                retry_memories.append(
                                    MemoryItem(
                                        id=getattr(item, "id", "") or "",
                                        text=getattr(item, "text", ""),
                                        category=category,
                                        tags=getattr(item, "tags", []) or [],
                                        context=getattr(item, "context", None),
                                        metadata=metadata if isinstance(metadata, dict) else {},
                                        score=float(score) if score is not None else None,
                                    )
                                )
                        return retry_memories, None
                    except Exception as retry_err:
                        logger.error(f"Retry recall after bank creation failed: {retry_err}")
                return [], f"Bank '{target_bank}' was created but currently contains no memories. Click 'Seed Standard Team Rules' to populate."
            return [], f"Hindsight API Error ({status}): {body}"
        except Exception as e:
            logger.exception("Error recalling memories from Hindsight")
            return [], f"Hindsight connection error: {str(e)}"

    def retain_knowledge(
        self,
        content: str,
        category: str = "team_standard",
        language: str = "general",
        source: str = "code_review",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, str]] = None,
        bank_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Store a reusable engineering lesson or standard into Hindsight memory.

        Args:
            content: Reusable rule, lesson, or preference statement
            category: 'team_standard', 'common_mistake', 'architectural_preference', or 'review_lesson'
            language: Programming language context
            source: Source of knowledge ('code_review', 'manual_seed', 'team_policy')
            tags: Specific tags for semantic filtering
            metadata: Custom key-value pairs
            bank_id: Target bank

        Returns:
            Tuple of (success boolean, status message)
        """
        if not self.is_available():
            return False, "HINDSIGHT_API_KEY not configured. Cannot retain knowledge."

        target_bank = (bank_id or self.config.hindsight_bank_id).strip()
        if not target_bank:
            return False, "HINDSIGHT_BANK_ID cannot be empty."

        cleaned_content = content.strip()
        if not cleaned_content:
            return False, "Cannot retain empty memory content."

        # Proactively ensure the bank exists before attempting retain
        if target_bank not in self._verified_banks:
            ok, bank_msg = self.ensure_bank_exists(target_bank)
            if not ok:
                logger.warning(f"Could not proactively ensure bank '{target_bank}' before retain: {bank_msg}")

        # Consolidate tags
        effective_tags = list(set([language.lower(), category.lower(), source.lower()] + (tags or [])))

        # Build metadata dictionary
        effective_meta = {
            "category": category,
            "language": language,
            "source": source,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if metadata:
            effective_meta.update({k: str(v) for k, v in metadata.items()})

        context_description = (
            f"Engineering team knowledge regarding {language} code standards and review findings."
        )

        try:
            # Official Hindsight retain method
            response = self._client.retain(
                bank_id=target_bank,
                content=cleaned_content,
                context=context_description,
                metadata=effective_meta,
                tags=effective_tags,
            )

            if response and getattr(response, "success", True):
                return True, f"Retained lesson in '{target_bank}': {cleaned_content[:80]}..."
            return False, "Hindsight returned unconfirmed retain status."

        except (ApiException, ClientResponseError) as e:
            status = getattr(e, "status", None)
            body = getattr(e, "body", None) or getattr(e, "message", None) or str(e)
            logger.error(f"Hindsight API error during retain ({status}): {body}")
            if status == 401:
                return False, "Authentication failed: Invalid Hindsight API Key."
            if status == 404:
                # Bank was missing; auto-heal by creating and retrying retain
                logger.info(f"Bank '{target_bank}' not found (404); attempting auto-creation and retry retain...")
                created_ok, _ = self.ensure_bank_exists(target_bank)
                if created_ok:
                    try:
                        retry_resp = self._client.retain(
                            bank_id=target_bank,
                            content=cleaned_content,
                            context=context_description,
                            metadata=effective_meta,
                            tags=effective_tags,
                        )
                        if retry_resp and getattr(retry_resp, "success", True):
                            return True, f"Retained lesson in '{target_bank}': {cleaned_content[:80]}..."
                    except Exception as retry_err:
                        logger.error(f"Retry retain after bank creation failed: {retry_err}")
            return False, f"Hindsight API Error ({status}): {body}"
        except Exception as e:
            logger.exception("Error retaining memory in Hindsight")
            return False, f"Hindsight retention error: {str(e)}"

    def seed_default_standards(self, bank_id: Optional[str] = None) -> Tuple[int, List[str]]:
        """
        Seed foundational team standards, recurring mistakes, and architectural preferences.
        Guarantees that the team starts with realistic organizational knowledge.
        """
        if not self.is_available():
            return 0, ["Cannot seed standards: HINDSIGHT_API_KEY is not configured."]

        target_bank = (bank_id or self.config.hindsight_bank_id).strip()

        # First ensure bank exists
        ok, msg = self.ensure_bank_exists(target_bank)
        if not ok:
            return 0, [f"Failed to initialize bank: {msg}"]

        foundational_rules = [
            {
                "content": (
                    "TEAM CODING STANDARD: Never construct SQL queries using string concatenation, "
                    "formatting strings, or f-strings with user input. Always use parameterized queries "
                    "or the approved team ORM (e.g. SQLAlchemy, Prisma, sqlx) to eliminate SQL injection."
                ),
                "category": "team_standard",
                "language": "sql",
                "tags": ["sql", "security", "injection", "standards"],
            },
            {
                "content": (
                    "COMMON MISTAKE / SECURITY RULE: Never expose raw system exceptions or stack traces "
                    "(e.g. str(e), traceback.format_exc(), e.getMessage()) in HTTP API responses to client callers. "
                    "Log internal error details securely on the server with a correlation/request ID, and return "
                    "sanitized, user-safe error messages."
                ),
                "category": "common_mistake",
                "language": "general",
                "tags": ["security", "error-handling", "api", "information-disclosure"],
            },
            {
                "content": (
                    "ARCHITECTURAL PREFERENCE: Maintain a strict layered architecture. Keep business, pricing, "
                    "and domain calculation logic out of controllers and HTTP route handlers. Controllers must only "
                    "handle request validation, session authentication, call domain service classes, and serialize responses."
                ),
                "category": "architectural_preference",
                "language": "general",
                "tags": ["architecture", "controllers", "service-layer", "clean-code"],
            },
            {
                "content": (
                    "TEAM CODING STANDARD: All public API endpoints and controller functions must validate and bounds-check "
                    "all incoming input parameters (e.g. positive amounts for transfers, allowable strings, schema checks) "
                    "before passing data to service or persistence layers."
                ),
                "category": "team_standard",
                "language": "general",
                "tags": ["validation", "security", "data-integrity"],
            },
        ]

        messages = []
        seeded_count = 0

        for rule in foundational_rules:
            success, status = self.retain_knowledge(
                content=rule["content"],
                category=rule["category"],
                language=rule["language"],
                source="manual_seed",
                tags=rule["tags"],
                bank_id=target_bank,
            )
            messages.append(status)
            if success:
                seeded_count += 1

        return seeded_count, messages

    def test_connection(self, bank_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Verify live connection and authentication with the Hindsight service.
        Guarantees that the bank exists before checking recall.
        """
        if not self.config.hindsight_api_key:
            return False, "Missing HINDSIGHT_API_KEY. Please provide your key in .env or settings."

        target_bank = (bank_id or self.config.hindsight_bank_id).strip()
        if not target_bank:
            return False, "Missing HINDSIGHT_BANK_ID."

        # Guarantee bank exists first
        ok, msg = self.ensure_bank_exists(target_bank)
        if not ok:
            return False, f"Failed to connect or configure bank '{target_bank}': {msg}"

        try:
            # Perform a test recall query to test full read capabilities
            response = self._client.recall(
                bank_id=target_bank,
                query="team engineering standards",
                budget="low",
                max_tokens=256,
            )
            count = len(response.results) if response and hasattr(response, "results") and response.results else 0
            return True, f"Successfully connected to Hindsight at {self.config.hindsight_api_url}. Bank '{target_bank}' ready ({count} memories matched)."
        except (ApiException, ClientResponseError) as e:
            status = getattr(e, "status", None)
            body = getattr(e, "body", None) or getattr(e, "message", None) or str(e)
            if status == 401:
                return False, f"Hindsight Authentication Failed (401): {body or 'Invalid API Key'}"
            return False, f"Hindsight API Error ({status}): {body}"
        except Exception as e:
            return False, f"Hindsight connection failed: {str(e)}"
