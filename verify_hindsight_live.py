"""
Live end-to-end verification of Hindsight memory bank and ReviewMind agent.
Verifies real Hindsight API and real Groq review execution.
"""

import sys
from pathlib import Path

# Fix Windows console encoding for emoji characters
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import get_settings
from src.memory import HindsightMemoryManager
from src.reviewer import CodeReviewer

def main():
    print("=" * 60)
    print("LIVE HINDSIGHT & REVIEWMIND INTEGRATION VERIFICATION")
    print("=" * 60)

    cfg = get_settings()
    print(f"Target Bank ID : {cfg.hindsight_bank_id}")
    print(f"Hindsight URL  : {cfg.hindsight_api_url}")
    print(f"Groq Model     : {cfg.groq_model}")

    # 1. Initialize Memory Manager
    print("\n[Step 1] Initializing HindsightMemoryManager...")
    mem_mgr = HindsightMemoryManager(cfg)
    assert mem_mgr.is_available(), "HindsightMemoryManager is not available! Check .env"
    print("   -> Manager initialized successfully.")

    # 2. Test Connection & Bank Verification
    print("\n[Step 2] Testing live connection and bank existence...")
    conn_ok, conn_msg = mem_mgr.test_connection()
    print(f"   Connection result: {conn_ok} | {conn_msg}")
    assert conn_ok, f"Connection failed: {conn_msg}"

    # 3. Seed Standards (Idempotent)
    print("\n[Step 3] Ensuring foundational standards exist in bank...")
    seeded_count, seed_msgs = mem_mgr.seed_default_standards()
    print(f"   Seeded {seeded_count} foundational rules.")
    for m in seed_msgs:
        print(f"   - {m}")

    # 4. Perform Real Recall from Bank
    print("\n[Step 4] Performing real recall query from Hindsight bank...")
    query = "SQL database queries and parameterized statements"
    memories, err = mem_mgr.recall_memories(query=query, budget="mid")
    print(f"   Recall query: '{query}'")
    print(f"   Error: {err}")
    print(f"   Recalled items: {len(memories)}")
    assert err is None, f"Recall returned error: {err}"
    assert len(memories) > 0, "Expected at least 1 recalled memory from bank!"
    for i, mem in enumerate(memories, 1):
        print(f"   [{i}] (Score: {mem.score}) {mem.text[:100]}...")

    # 5. Perform Real Retain into Bank
    print("\n[Step 5] Performing real retain into Hindsight bank...")
    test_lesson = "ARCHITECTURAL RULE: Always sanitize inputs and enforce pagination for database record queries."
    retain_ok, retain_msg = mem_mgr.retain_knowledge(
        content=test_lesson,
        category="architectural_preference",
        language="python",
        source="e2e_test",
        tags=["python", "pagination", "architecture"],
    )
    print(f"   Retain result: {retain_ok} | {retain_msg}")
    assert retain_ok, f"Retain failed: {retain_msg}"

    # 6. Execute Full Real Review with Groq + Hindsight
    print("\n[Step 6] Running full live review with Groq LLM + Hindsight memory...")
    reviewer = CodeReviewer(config=cfg, memory_manager=mem_mgr)
    vulnerable_code = '''
def get_user_profile(user_id):
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    return db.execute(query).fetchall()
'''
    result, logs = reviewer.review(
        code=vulnerable_code,
        language="python",
        use_memory=True,
        auto_retain=True,
    )

    print("\n   --- Execution Logs ---")
    for log in logs:
        print(f"   {log}")

    print("\n   --- Review Result ---")
    print(f"   Risk: {result.risk}")
    print(f"   Summary: {result.summary}")
    print(f"   Issues found: {len(result.issues)}")
    for issue in result.issues:
        print(f"     * [{issue.severity.upper()}] {issue.title}: {issue.why[:80]}...")
    print(f"   Team rules used: {result.team_rules_used}")
    print(f"   Learned lessons: {result.learning}")
    print(f"   Retention status: {result.retention_status}")

    assert result.risk in ["critical", "high"], f"Expected high/critical risk, got {result.risk}"
    assert len(result.issues) > 0, "Expected at least 1 issue"
    assert not any("404" in log for log in logs), "Logs contained a 404 error!"
    assert not any("Bank 'reviewmind-team' not found" in log for log in logs), "Logs contained bank not found!"

    print("\n" + "=" * 60)
    print("ALL LIVE VERIFICATION CHECKS PASSED WITH REAL APIS! (6/6)")
    print("=" * 60)

if __name__ == "__main__":
    main()
