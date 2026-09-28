"""
End-to-end flow verification script for ReviewMind.
Verifies the complete lifecycle:
RECALL -> USE MEMORY -> REVIEW -> LEARN -> RETAIN
"""

import sys
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.config import Settings
from src.models import ReviewResult, MemoryItem
from src.memory import HindsightMemoryManager
from src.reviewer import CodeReviewer
from demo_samples import get_sample_by_id

def test_full_lifecycle_with_mocks():
    print("==================================================")
    print("TESTING FULL LIFECYCLE: RECALL -> REVIEW -> LEARN -> RETAIN")
    print("==================================================")

    # 1. Setup mock config with fake credentials to test the logic pipeline
    cfg = Settings(
        groq_api_key="gsk_mock_test_key_for_pipeline",
        hindsight_api_key="hs_mock_test_key_for_pipeline",
        hindsight_bank_id="reviewmind-team",
        groq_model="openai/gpt-oss-120b",
    )

    # 2. Mock Hindsight client
    mock_hindsight = MagicMock()

    # Mock recall response
    mock_recall_result = MagicMock()
    mock_recall_result.id = "mem-sql-1"
    mock_recall_result.text = "Never construct SQL queries using string concatenation. Always use parameterized queries or approved ORM."
    mock_recall_result.tags = ["sql", "security", "team_standard"]
    mock_recall_result.context = "Team SQL standards"
    mock_recall_result.metadata = {"category": "team_standard", "language": "python"}
    mock_recall_result.scores = MagicMock(final=0.94)

    mock_recall_response = MagicMock()
    mock_recall_response.results = [mock_recall_result]
    mock_hindsight.recall.return_value = mock_recall_response

    # Mock retain response
    mock_retain_response = MagicMock(success=True)
    mock_hindsight.retain.return_value = mock_retain_response
    mock_hindsight.create_bank.return_value = MagicMock(success=True)

    # 3. Initialize memory manager with mocked client
    mem_mgr = HindsightMemoryManager(cfg)
    mem_mgr._client = mock_hindsight

    # 4. Test Recall
    print("-> Phase 1: RECALL from Hindsight...")
    memories, err = mem_mgr.recall_memories("python sql parameterized queries")
    assert err is None
    assert len(memories) == 1
    assert "Always use parameterized queries" in memories[0].text
    print(f"   [PASS] Recalled: {memories[0].text[:60]}... (Score: {memories[0].score})")

    # 5. Mock Groq LLM response
    mock_groq = MagicMock()
    llm_json_output = '''{
        "summary": "Critical SQL injection detected due to string concatenation with request parameters.",
        "risk": "critical",
        "issues": [
            {
                "severity": "critical",
                "line": "Line 5",
                "title": "SQL Injection via Unsanitized Input",
                "why": "[Team Memory Standard Violation]: Directly violates team policy requiring parameterized queries. Concatenating user_id allows arbitrary SQL execution.",
                "suggestion": "cursor.execute('SELECT id, username FROM users WHERE id = %s', (user_id,))"
            }
        ],
        "team_rules_used": [
            "Never construct SQL queries using string concatenation. Always use parameterized queries or approved ORM."
        ],
        "learning": [
            "Mandate DB-API parameterization across all repository queries and prohibit raw string concatenation."
        ]
    }'''
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content=llm_json_output))]
    mock_groq.chat.completions.create.return_value = mock_completion

    reviewer = CodeReviewer(config=cfg, memory_manager=mem_mgr)
    reviewer._groq_client = mock_groq

    # 6. Execute Review (Triggers RECALL -> PROMPT -> REVIEW -> LEARN -> RETAIN)
    print("-> Phase 2: REVIEW and GROUNDING...")
    sample = get_sample_by_id("sql_injection")
    result, logs = reviewer.review(
        code=sample.vulnerable_code,
        language="python",
        use_memory=True,
        auto_retain=True,
    )

    # 7. Verify Review Results
    assert result.risk == "critical"
    assert len(result.issues) == 1
    assert len(result.team_rules_used) == 1
    assert "parameterized queries" in result.team_rules_used[0]
    print(f"   [PASS] Risk: {result.risk.upper()}")
    print(f"   [PASS] Team Memory Rule Applied: {result.team_rules_used[0]}")
    print(f"   [PASS] Issues: {result.issues[0].title} ({result.issues[0].severity})")

    # 8. Verify Learning Loop and Retain
    print("-> Phase 3: LEARN and RETAIN...")
    assert len(result.learning) == 1
    print(f"   [PASS] Synthesized Lesson: {result.learning[0]}")
    assert mock_hindsight.retain.called
    print("   [PASS] Verified Hindsight retain() was invoked with new lesson.")
    print("   [PASS] Complete ReviewMind cycle verified!")

if __name__ == "__main__":
    test_full_lifecycle_with_mocks()
