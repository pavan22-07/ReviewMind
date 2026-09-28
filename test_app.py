"""
Automated verification script for ReviewMind.
Tests imports, configurations, models, demo samples, prompts, error handling,
resilient parsing, and execution without credentials.
"""

import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def test_imports():
    print("-> 1. Testing imports...")
    import src.config
    import src.models
    import src.memory
    import src.prompts
    import src.reviewer
    import demo_samples
    print("   [PASS] All modules imported successfully.")

def test_config():
    print("-> 2. Testing config and missing credentials reporting...")
    from src.config import Settings, get_settings, update_settings

    cfg = get_settings()
    assert cfg.hindsight_bank_id == "reviewmind-team"
    assert cfg.groq_model == "openai/gpt-oss-120b"
    assert cfg.hindsight_api_url == "https://api.hindsight.vectorize.io"

    missing_msg = cfg.get_missing_credentials_message()
    print(f"   Config diagnostics message:\n   {missing_msg.replace(chr(10), chr(10) + '   ')}")
    print("   [PASS] Configuration validation is working properly.")

def test_models():
    print("-> 3. Testing data models...")
    from src.models import ReviewIssue, ReviewResult, MemoryItem

    issue = ReviewIssue(
        severity="critical",
        line="Line 4",
        title="SQL Injection",
        why="Concatenating user input into SQL violates team standard.",
        suggestion="cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))"
    )
    assert issue.severity == "critical"

    result = ReviewResult(
        summary="Found 1 critical issue.",
        risk="critical",
        issues=[issue],
        team_rules_used=["Always use parameterized queries."],
        learning=["Enforce parameterized queries across all database queries."],
        used_memory=True,
    )
    assert len(result.issues) == 1
    assert len(result.team_rules_used) == 1
    assert result.used_memory is True
    print("   [PASS] Pydantic models validated successfully.")

def test_demo_samples():
    print("-> 4. Testing demo samples...")
    from demo_samples import DEMO_SAMPLES, get_sample_by_id

    assert len(DEMO_SAMPLES) >= 4, f"Expected at least 4 demo samples, got {len(DEMO_SAMPLES)}"
    required_ids = ["sql_injection", "raw_exception", "missing_validation", "controller_business_logic"]
    sample_ids = [s.id for s in DEMO_SAMPLES]

    for rid in required_ids:
        assert rid in sample_ids, f"Missing required sample: {rid}"
        sample = get_sample_by_id(rid)
        assert len(sample.vulnerable_code) > 0
        assert len(sample.fixed_code) > 0
        assert len(sample.expected_team_rule) > 0
        print(f"   [PASS] Sample '{sample.title}' verified.")

def test_prompts():
    print("-> 5. Testing prompts generation...")
    from src.prompts import SYSTEM_PROMPT, build_review_user_prompt

    user_prompt = build_review_user_prompt(
        code="query = 'SELECT * FROM users WHERE id = ' + user_id",
        language="python",
        recalled_memories=["Always use parameterized queries or approved ORM."],
    )
    assert "RECALLED TEAM MEMORY" in user_prompt
    assert "Always use parameterized queries" in user_prompt
    assert "SELECT * FROM users" in user_prompt
    assert "CRITICAL RULES FOR REVIEW" in SYSTEM_PROMPT
    print("   [PASS] Prompts constructed with memory grounding.")

def test_resilient_parser():
    print("-> 6. Testing JSON parsing resilience and fallback...")
    from src.reviewer import CodeReviewer

    reviewer = CodeReviewer()
    
    # Valid JSON
    valid_json = '''{
        "summary": "Clean code",
        "risk": "low",
        "issues": [],
        "team_rules_used": [],
        "learning": ["Maintain clean functions"]
    }'''
    res = reviewer._parse_json_response(valid_json, "python", "openai/gpt-oss-120b", True, [], [])
    assert res.risk == "low"
    assert len(res.learning) == 1

    # Markdown wrapped JSON
    wrapped_json = f"```json\n{valid_json}\n```"
    res_wrapped = reviewer._parse_json_response(wrapped_json, "python", "openai/gpt-oss-120b", True, [], [])
    assert res_wrapped.risk == "low"

    # Malformed text fallback
    malformed = "I found a bug in line 5. It should be parameterized."
    res_fallback = reviewer._parse_json_response(malformed, "python", "openai/gpt-oss-120b", False, [], [])
    assert res_fallback.risk == "medium"
    assert len(res_fallback.issues) == 1
    assert "LLM Review Findings" in res_fallback.issues[0].title
    print("   [PASS] Resilient JSON parser and fallback tested successfully.")

def test_missing_credentials_behavior():
    print("-> 7. Testing missing credentials behavior...")
    from src.config import Settings
    from src.reviewer import CodeReviewer
    from src.memory import HindsightMemoryManager

    # Use explicit empty settings to test missing credentials branch
    empty_cfg = Settings(groq_api_key="", hindsight_api_key="")
    mem_mgr = HindsightMemoryManager(config=empty_cfg)
    ok, msg = mem_mgr.test_connection()
    assert not ok
    assert "HINDSIGHT_API_KEY" in msg
    print(f"   Memory connection check without key: {msg}")

    # Recall without key
    memories, err = mem_mgr.recall_memories(query="test query")
    assert len(memories) == 0
    assert "HINDSIGHT_API_KEY" in err
    print(f"   Memory recall without key: {err}")

    # Retain without key
    ret_ok, ret_msg = mem_mgr.retain_knowledge(content="test content")
    assert not ret_ok
    assert "HINDSIGHT_API_KEY" in ret_msg
    print(f"   Memory retain without key: {ret_msg}")

    # Review without key
    reviewer = CodeReviewer(config=empty_cfg, memory_manager=mem_mgr)
    rev_result, logs = reviewer.review(code="def test(): pass", language="python", use_memory=True)
    assert "GROQ_API_KEY is not configured" in rev_result.summary or any("GROQ_API_KEY" in iss.title for iss in rev_result.issues)
    print(f"   Review without key: Handled cleanly without crash. Issues: {[i.title for i in rev_result.issues]}")
    print("   [PASS] Robust missing credentials handling verified.")

def main():
    print("==================================================")
    print("RUNNING REVIEWMIND TEST SUITE")
    print("==================================================")
    test_imports()
    test_config()
    test_models()
    test_demo_samples()
    test_prompts()
    test_resilient_parser()
    test_missing_credentials_behavior()
    print("==================================================")
    print("ALL TESTS PASSED SUCCESSFULLY! (7/7)")
    print("==================================================")

if __name__ == "__main__":
    main()
