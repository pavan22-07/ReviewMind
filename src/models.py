"""
Data models and schemas for ReviewMind.
Defines structured schemas for code review results, issues, and memory items.
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class ReviewIssue(BaseModel):
    """Individual code review issue or finding."""

    severity: Literal["critical", "high", "medium", "low"] = Field(
        ...,
        description="Severity level of the issue: critical, high, medium, or low",
    )
    line: str = Field(
        ...,
        description="Line number or line range affected, e.g. 'Line 4' or 'Line 12-16'",
    )
    title: str = Field(
        ...,
        description="Brief, clear summary title of the issue",
    )
    why: str = Field(
        ...,
        description="Detailed explanation of why this is problematic, potential security/performance impact, and relevant context",
    )
    suggestion: str = Field(
        ...,
        description="Actionable recommendation and concrete code fix snippet",
    )


class ReviewResult(BaseModel):
    """Complete structured code review output returned by ReviewMind."""

    summary: str = Field(
        ...,
        description="Executive summary of the overall code quality and review findings",
    )
    risk: Literal["critical", "high", "medium", "low"] = Field(
        ...,
        description="Overall risk rating of the code snippet",
    )
    issues: List[ReviewIssue] = Field(
        default_factory=list,
        description="List of identified issues and actionable suggestions",
    )
    team_rules_used: List[str] = Field(
        default_factory=list,
        description="List of explicit team rules/standards retrieved from Hindsight memory that were applied during this review",
    )
    learning: List[str] = Field(
        default_factory=list,
        description="Reusable, generalizable lessons or standards extracted from this review to be stored in Hindsight for future reviews",
    )

    # Metadata fields (populated by ReviewMind runner)
    used_memory: bool = Field(
        default=False,
        description="True if Hindsight team memory was recalled and provided to the LLM",
    )
    recalled_memories: List[str] = Field(
        default_factory=list,
        description="Raw team memory statements retrieved from Hindsight and injected into prompt",
    )
    language: str = Field(
        default="python",
        description="Programming language of the reviewed code",
    )
    model: str = Field(
        default="openai/gpt-oss-120b",
        description="LLM model used for the review",
    )
    retention_status: List[str] = Field(
        default_factory=list,
        description="Status messages for retained lessons in Hindsight",
    )


class MemoryItem(BaseModel):
    """Structured representation of a team memory recalled from or retained into Hindsight."""

    id: str = Field(default="", description="Unique identifier of the memory unit")
    text: str = Field(..., description="The memory content or standard statement")
    category: str = Field(
        default="team_standard",
        description="Category: team_standard, common_mistake, architectural_preference, or review_lesson",
    )
    tags: List[str] = Field(default_factory=list, description="Descriptive tags")
    context: Optional[str] = Field(
        default=None, description="Additional context or rationale"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Metadata dictionary associated with memory"
    )
    score: Optional[float] = Field(
        default=None, description="Retrieval similarity score from Hindsight"
    )


class DemoSample(BaseModel):
    """A pre-configured code sample for interactive hackathon demonstration."""

    id: str
    title: str
    language: str
    category: str
    description: str
    vulnerable_code: str
    fixed_code: str
    expected_team_rule: str
    why_it_matters: str
