# ReviewMind – UI Fix Specification for Agent Execution

> **Scope:** Only `app.py` (Streamlit presentation layer) may be modified.  
> Do NOT touch: `src/memory.py`, `src/reviewer.py`, `src/prompts.py`, `src/models.py`, `src/config.py`, `demo_samples.py`, any test files, or `.env`.

---

## Summary of Required Changes

| # | Area | What to Change |
|---|------|----------------|
| 1 | Sidebar navigation | Remove "📜 Review History", "⚙️ Settings", "ℹ️ Architecture" from nav |
| 2 | Pipeline strip | Remove the 6-step pipeline block from the Code Review view |
| 3 | Code Review layout | Rename headers, label columns as explicit INPUT / OUTPUT |
| 4 | Architecture page | Replace with a clean in-line Architecture section (no separate nav) |
| 5 | Settings relocation | Move API key / bank / model settings into the **sidebar** (collapsible) |
| 6 | Theme enforcement | Force always-dark theme; remove any light-mode CSS fallbacks |
| 7 | Sidebar cleanup | Remove redundant captions, reduce clutter, only keep what is useful |

---

## Fix 1 – Sidebar Navigation Reduction

### Problem
The left sidebar navigation radio list currently contains 7 options:
```
🔍 Code Review
🧠 Team Memory
📜 Review History     ← REMOVE
📊 Analytics
🧪 Interactive Demo
⚙️ Settings           ← REMOVE (move content to sidebar)
ℹ️ Architecture       ← REMOVE (fold into Team Memory or Architecture inline section)
```

### What to do
**File:** `app.py` — lines ~398–411

Reduce the `nav_option` radio to exactly **4 options**:
```python
nav_option = st.radio(
    "NAVIGATION",
    options=[
        "🔍 Code Review",
        "🧠 Team Memory",
        "📊 Analytics",
        "🧪 Interactive Demo",
    ],
    index=0,
    label_visibility="collapsed",
)
```

Delete the entire `elif nav_option == "📜 Review History":` block (lines ~999–1044).  
Delete the entire `elif nav_option == "⚙️ Settings":` block (lines ~1288–1337).  
Delete the entire `elif nav_option == "ℹ️ Architecture":` block (lines ~1343–1403).

---

## Fix 2 – Remove the Pipeline Diagram Strip

### Problem
At the bottom of the Code Review view (after the two columns), there is a wide "🔄 ORGANIZATIONAL MEMORY PIPELINE" card that renders a 6-step flow with arrows. It adds visual noise without conveying useful runtime information.

### What to do
**File:** `app.py` — lines ~790–841

Delete everything from:
```python
# MEMORY VISUALIZATION PIPELINE (Always visible beneath editor)
st.markdown("<div style='height: 20px;'></div>", ...)
st.markdown("""
    <div class="dash-card">
        <div style="...">🔄 ORGANIZATIONAL MEMORY PIPELINE</div>
        ...
    </div>
""", ...)
```

This is a self-contained block and removing it has zero effect on review logic.

---

## Fix 3 – Code Review Column Labeling (Input / Output Clarity)

### Problem
The two-column layout labels are:
- Left: `"1. Source Code Input"` (acceptable, but vague)
- Right: `"2. Grounded Findings & Analysis"` (not explicitly "Output")

The user needs to instantly understand what they should interact with (left = input) and what the system produces (right = output).

### What to do
**File:** `app.py` — lines ~483–609

**Left column header** (line ~488): Change label from:
```python
"1. Source Code Input"
```
To:
```python
"📥 INPUT — Paste or Select Source Code"
```

**Right column header** (line ~604): Change label from:
```python
"2. Grounded Findings & Analysis"
```
To:
```python
"📤 OUTPUT — Review Findings & Memory Applied"
```

Also rename the run button (line ~554) from:
```python
"🚀 Execute ReviewMind Review"
```
To:
```python
"🚀 Run Review"
```
(Shorter and cleaner.)

---

## Fix 4 – Architecture & Settings: Move Into Sidebar Instead of Separate Pages

### Problem
- **Settings** is a full-page navigation entry but contains just a few text inputs and a save button. Requiring the user to navigate away from Code Review to change a key is disruptive.
- **Architecture** is pure static informational content occupying a top-level navigation slot, which crowds the nav.

### What to do

#### 4a – Settings block moved INTO sidebar

**File:** `app.py` — sidebar block, after the Ping Test / Seed Rules buttons (~line 466+)

Add a collapsible `st.expander("⚙️ Configure Keys & Model")` within the sidebar that contains:
- `Groq API Key` (password input)
- `Hindsight API Key` (password input)  
- `Hindsight Bank ID` (text input)
- `Groq Model` (selectbox)
- `Apply Settings` button

This logic is a copy of the existing Settings page inputs — move it here and wire it to the same `update_settings()` call. The full-page Settings view should then be deleted (per Fix 1).

Do NOT expose `Hindsight API Host URL` in the sidebar — this is an advanced/infrastructure setting that most users should not need to change. Leave it only configurable via `.env`.

#### 4b – Architecture block as an inline expander inside Team Memory page

**File:** `app.py` — `elif nav_option == "🧠 Team Memory":` block

At the **bottom** of the Team Memory page, add a `st.expander("ℹ️ How ReviewMind Works (Architecture)")` that contains the plain-text architecture diagram from the current Architecture page (the ASCII block). This way the information is accessible without a nav entry.

Remove the top-level Architecture nav option (already covered in Fix 1).

---

## Fix 5 – Enforce Always-Dark Theme

### Problem
The `st.set_page_config()` does not enforce dark theme explicitly. Streamlit can render in the user's system preference, which may be light on some machines. The user reports the UI feels inconsistently dark.

### What to do

**File:** `app.py` — `st.set_page_config()` call (~lines 19–24)

Enforce the theme using Streamlit's `theme` parameter:
```python
st.set_page_config(
    page_title="ReviewMind | Team Memory Code Review Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)
```

Then add an explicit CSS override at the very beginning of the `<style>` block to prevent any light-mode bleed. Replace any existing global background CSS with:
```css
/* Force Always-Dark: override Streamlit theme variables */
:root {
    --background-color: #090514 !important;
    --secondary-background-color: #120C24 !important;
    --text-color: #F8FAFC !important;
}
html, body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stHeader"], [data-testid="stSidebar"],
section[data-testid="stSidebarContent"] {
    background-color: #090514 !important;
    color: #F8FAFC !important;
}
```

Also add to the existing CSS:
```css
/* Sidebar always dark */
[data-testid="stSidebar"] {
    background-color: #0C0820 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
}
```

---

## Fix 6 – Sidebar Cleanup

### Problem
The bottom of the sidebar currently shows:
```
st.caption("Active Bank: `reviewmind-team`")
st.caption("Model: `openai/gpt-oss-120b`")
```
These are useful but presented as plain captions without visual weight. The sidebar also shows only 2 quick-action buttons (Ping Test, Seed Rules), which are fine to keep.

### What to do

**File:** `app.py` — sidebar block (~lines 466–468)

Replace the plain `st.caption()` lines with a styled block that integrates the active bank and model info into the Intelligence Engine status card (the card already exists from lines ~424–445). Extend that card's HTML to include:
```html
<div style="border-top: 1px solid rgba(255,255,255,0.05); margin-top: 10px; padding-top: 8px; font-size: 0.72rem; color: #4B5563;">
    Bank: <span style="color: #A78BFA;">reviewmind-team</span><br/>
    Model: <span style="color: #A78BFA;">openai/gpt-oss-120b</span>
</div>
```
(Replace the hardcoded strings with `st.session_state.config.hindsight_bank_id` and `st.session_state.config.groq_model` using f-string in the existing f-string HTML block.)

Remove the standalone `st.caption()` lines.

---

## Session State and Logic Preservation Notes

- **`st.session_state.review_history`** is still populated on every review run (for Analytics). Do NOT remove history-tracking logic from the `if run_btn:` block (~lines 581–597). The Review History page is removed from the UI, but the session data backing Analytics must remain.
- **`st.session_state.last_review`** and **`st.session_state.last_generic_review`** must remain in session state initialization.
- All Hindsight memory recall/retain calls in `reviewer.review()` are untouched.
- The `resolve_team_rule_text()` helper function (lines ~289–324) must NOT be removed.
- The `get_severity_badge()` and `get_risk_badge()` helpers must NOT be removed.

---

## Resulting Navigation Structure After Fixes

```
Sidebar (always visible):
  ┌─ 🧠 ReviewMind [logo]
  ├─ INTELLIGENCE ENGINE status card (Groq + Hindsight dots, Bank, Model)
  ├─ [🔌 Ping Test]  [🌱 Seed Rules]
  ├─ ⚙️ Configure Keys & Model  ← collapsible expander
  └─ Navigation:
       ● 🔍 Code Review        (default)
       ○ 🧠 Team Memory
       ○ 📊 Analytics
       ○ 🧪 Interactive Demo

Main content area:
  Code Review:
    [📥 INPUT — left column]  |  [📤 OUTPUT — right column]
    (no pipeline strip below)
```

---

## CSS Classes to Check and Preserve

These CSS class names are referenced throughout `app.py`'s HTML strings and must remain in the `<style>` block:

| Class | Used For |
|-------|---------|
| `.stApp` | Global background |
| `.brand-title` | Page heading gradient text |
| `.brand-tagline` | Subtitle text |
| `.dash-card` | General dark info card |
| `.dash-card-glow` | Highlighted card with magenta glow |
| `.metric-card` | Small metric boxes (4-column grid) |
| `.metric-value` | Large number inside metric card |
| `.metric-label` | Small label inside metric card |
| `.badge-critical` | Severity pill |
| `.badge-high` | Severity pill |
| `.badge-medium` | Severity pill |
| `.badge-low` | Severity pill |
| `.badge-magenta` | "Hindsight Active" pill |
| `.memory-applied-container` | The purple-bordered Hindsight memory block |
| `.memory-rule-card` | Individual team standard card inside memory block |
| `.pipe-step` | Pipeline step card (can be deleted with Fix 2) |
| `.pipe-step-active` | Active pipeline step (can be deleted with Fix 2) |

---

## What NOT to Change

- Do NOT modify any logic in `src/` directory files.
- Do NOT change `DEMO_SAMPLES`, `get_sample_by_id()` in `demo_samples.py`.
- Do NOT change LLM prompts in `src/prompts.py`.
- Do NOT change Hindsight API integration in `src/memory.py`.
- Do NOT remove the `resolve_team_rule_text()` function from `app.py`.
- Do NOT change the Code Review execution flow (`if run_btn:` block).
- Do NOT alter the Interactive Demo (`🧪 Interactive Demo`) page — it is clean and useful.
- Do NOT alter the Team Memory (`🧠 Team Memory`) page except adding the Architecture expander at the bottom.
- Do NOT alter the Analytics (`📊 Analytics`) page.
