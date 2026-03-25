# SmartMed Review 4.2 — Comprehensive Technical Specification (Streamlit on Hugging Face Spaces)

**Document Version:** 4.2.0  
**Date:** 2026-03-25  
**Status:** Draft Technical Specification (Design + Implementation Guidance; **no code included**)  
**System Name:** SmartMed Review 4.2 (智慧醫材審查指引與清單生成系統)  
**Deployment Target:** Hugging Face Spaces (Streamlit)  
**Core Stack:** Streamlit + `agents.yaml` + Multi-LLM routing (Gemini / OpenAI / Anthropic / Grok) + PDF/OCR toolchain

---

## 1. Executive Summary

SmartMed Review 4.2 is an AI-powered, agentic regulatory workspace for medical device Regulatory Affairs (RA) teams and reviewer workflows. It **retains all original capabilities** of SmartMed Review 3.x/4.0/4.1—document ingestion, PDF preview and page selection, OCR (Python OCR + Gemini Vision OCR), guidance transformation into structured Markdown, 510(k) intelligence utilities, checklists and report drafting, dynamic agent orchestration via `agents.yaml`, SKILL panel rendering, and AI Note Keeper with editable inputs/outputs.

Version **4.2** focuses on **WOW-level user experience upgrades** and **fine-grained human-in-the-loop control** across the full agent pipeline, while extending the AI Note Keeper with **three additional AI features** (in addition to the existing six “AI Magics”). It also formalizes **three enhanced WOW visualization features**: **WOW Interactive Indicator**, **Live Log**, and **WOW Interactive Dashboard** with deeper interactivity, drilldowns, and observability.

### 1.1 Key Additions in 4.2 (Compared to 4.1)

1. **WOW UI v2** (new “WOW UI” layer maintained across the app)
   - Theme toggle: **Light / Dark**
   - Language toggle: **English / Traditional Chinese (繁體中文)**
   - **20 painter-inspired styles** (based on famous painters; style selectable or randomized via “Jackpot”)
   - Unified design tokens (color, typography, spacing, motion) applied consistently to all modules

2. **WOW Visualization Enhancements (3 features)**
   - **WOW Interactive Indicator**: agent/module run states with interactive drilldowns and status storytelling
   - **Live Log**: streaming events + filter/search + structured run events + export
   - **WOW Interactive Dashboard**: cross-module analytics, run timelines, model mix, token/cost estimates, and “bottleneck” insights

3. **API Key Handling: Environment-first + UI fallback**
   - Users can input provider keys in the web UI **only if missing in environment**
   - If a key exists in environment, UI shows “Managed by environment” and **never displays the key**
   - Session-only storage for UI-entered keys, never logged, never persisted

4. **Agent-by-agent execution studio**
   - Before running each agent:
     - user can **select model** (from allowlist)
     - **modify the prompt**
     - adjust parameters (max tokens, temperature)
   - After each agent run:
     - output is editable in **Text or Markdown view**
     - the edited output becomes the input for the next agent
   - Supports sequential execution with explicit “Run Next” controls and clear run-state UI

5. **AI Note Keeper expansion**
   - Paste notes (TXT/Markdown), transform into organized Markdown with **keywords highlighted in coral**
   - Toggle editing in Markdown or TXT view
   - Keep a custom prompt for further transformations OR apply AI Magics
   - **Adds 3 new AI Magics** (bringing the total to **9**)

6. **Multi-provider model selection expansion (standardized lists)**
   - OpenAI: `gpt-4o-mini`, `gpt-4.1-mini`
   - Gemini: `gemini-2.5-flash`, `gemini-3-flash-preview`
   - Anthropic: configurable “claude-*” family (e.g., `claude-3.5-sonnet`, `claude-3.5-haiku`, subject to account availability)
   - Grok: `grok-4-fast-reasoning`, `grok-3-mini`
   - Model availability is validated by provider-key presence + allowlist rules per module

---

## 2. Users, Use Cases, and Success Criteria

### 2.1 Primary Users
- **Regulatory Affairs specialists**: interpret guidance, prepare submission strategy, generate checklists
- **Medical device reviewers**: triage submissions, identify gaps, draft review memos and requests
- **Quality/compliance professionals**: ensure traceability, completeness, and process consistency
- **Technical leads**: maintain `agents.yaml`, validate prompts/skills, deploy on Hugging Face Spaces

### 2.2 Key User Journeys
1. **Guidance ingestion → OCR → Structured guidance Markdown**  
   Upload PDF, select pages, OCR/extract, generate structured reviewer-friendly guidance doc (with constraint checks).

2. **Agent pipeline execution with editing between agents**  
   Execute agents sequentially; customize prompts and models step-by-step; edit outputs before passing onward.

3. **AI Note Keeper**  
   Paste messy notes → receive organized Markdown with coral keywords → refine → apply AI Magics (9) using chosen models.

4. **Operational monitoring & debugging (WOW Observability)**  
   Use Interactive Indicator + Live Log + Dashboard to understand what ran, what failed, time/cost, and bottlenecks.

### 2.3 Definition of “Excellent Results”
- Users can **control** every major generation step (prompt, model, parameters, input/output edits)
- Outputs are reproducible and explainable via pinned prompts + run metadata
- Errors are understandable and actionable (preflight checks; consistent statuses)
- WOW UI feels cohesive, modern, and delightful without obscuring transparency

---

## 3. Scope, Non-Goals, and Design Principles

### 3.1 In-Scope Modules (All Original Features Preserved)
- WOW Dashboard + status + metrics
- Guidance Workspace:
  - Paste/upload TXT/MD/PDF
  - PDF preview + page selection
  - OCR/extraction (Python extraction + optional OCR; Gemini Vision OCR)
  - Structured guidance Markdown generation (2000–3000 words, exactly 3 tables)
  - Edit + download
- 510(k) intelligence utilities (PDF → Markdown transformer, summary/entities, comparator)
- Checklist & report drafting tools
- AI Note Keeper (now with 9 Magics)
- FDA orchestration + dynamic agents from guidance
- `agents.yaml` based orchestration
- SKILL panel rendering (`SKILL.md`)

### 3.2 Non-Goals (Explicit)
- No multi-user authentication, RBAC, audit database, or enterprise tenancy requirements
- No legal/regulatory authority claims; outputs are drafting aids
- No guaranteed deterministic compliance; LLMs are probabilistic
- No long-term server-side storage requirement (session-based by default)

### 3.3 Design Principles
- **Human-in-the-loop as default**: no black-box batch pipelines
- **Environment-first security**: keys from environment secrets take priority; UI fallback is optional and session-only
- **Provider-agnostic orchestration**: one unified LLM interface across providers
- **Graceful degradation**: core ingestion works even if optional OCR dependencies missing
- **WOW UX with observability**: make status, logs, and run artifacts first-class

---

## 4. High-Level Architecture

### 4.1 Runtime Components
**A. Streamlit UI Layer**
- Sidebar: global settings (theme, language, painter style, jackpot, default model/params), API key manager, optional `agents.yaml` override upload
- Main area: module tabs and workflow steps
- Persistent top status bar: WOW indicator + quick actions (clear session, export logs, download artifacts)

**B. Session State Layer (Ephemeral)**
Stores runtime-only artifacts:
- Uploaded PDF bytes (per file)
- Page selections + rendered thumbnails (if enabled)
- Extracted raw text per page + merged guidance text
- Generated guidance Markdown + compliance check results
- Agent prompts, pinned prompts, outputs (editable)
- Run events (structured) for live log/dashboard
- Session-only provider keys if entered via UI

**C. Document Processing Layer**
- PDF text extraction via `pypdf` (best-effort)
- PDF page rendering to images via PyMuPDF/Pillow (optional)
- Python OCR via pytesseract (optional; if dependencies installed)
- Gemini Vision OCR option for scanned documents

**D. LLM Integration Layer**
Unified routing by model name:
- OpenAI (Chat Completions)
- Gemini (generate_content)
- Anthropic (messages)
- Grok/xAI REST

**E. Agent Orchestration Layer**
- Agents defined in `agents.yaml` (system prompt, templates, defaults)
- Agent Studio UI supports:
  - pre-run editing of prompt and model
  - post-run editing of output
  - chaining output to next agent
  - run metadata capture (time, model, estimated tokens)

### 4.2 Cross-Cutting Concerns
- **Preflight validation**: block runs before they start if keys/models/inputs missing
- **Observability**: each run emits structured events to Live Log + Dashboard
- **Consistency**: WOW UI v2 design tokens applied across all modules

---

## 5. WOW UI v2 (Theme, Language, Painter Styles, Jackpot)

### 5.1 Global Controls
Accessible from sidebar and mirrored in a compact header menu:
- **Theme**: Light / Dark
- **Language**: English / Traditional Chinese  
  - Applies to UI labels, help text, warnings, and system messages  
  - (Generated content language remains controlled by prompts and module toggles.)
- **Painter Style (20)**: aesthetic overlay controlling gradients, background textures, accent harmonies
- **Jackpot**: randomly selects a painter style (with optional “lock style for this session”)

### 5.2 Painter Style Set (20 Styles)
Painter-inspired style presets define:
- background gradient palette
- accent color harmonies
- panel border glow intensity
- button style (solid vs glass vs outline)
- motion profile (subtle vs energetic)

**Example list (names used as UI labels; no IP assets embedded):**
1. Monet (soft atmospheric)
2. Van Gogh (high contrast strokes)
3. Picasso (geometric blocks)
4. Klimt (golden ornament)
5. Hokusai (indigo waves)
6. Rothko (color fields)
7. Pollock (speckled energy)
8. Vermeer (calm light)
9. Matisse (bold cut-outs)
10. Rembrandt (chiaroscuro)
11. Turner (mist + glow)
12. Cézanne (structured depth)
13. Magritte (surreal clarity)
14. Dalí (dream distortion)
15. Kandinsky (abstract rhythm)
16. Hopper (quiet modern)
17. O’Keeffe (organic minimal)
18. Basquiat (street annotation)
19. Bruegel (dense detail)
20. Ukiyo-e (woodblock flatness)

### 5.3 Design Tokens and Accessibility
- Typography scale with clear hierarchy (H1/H2/H3, body, monospace for logs)
- Minimum contrast ratios maintained in both themes
- Keyboard navigability:
  - tab focus states
  - action buttons reachable in order
- Coral highlight color reserved for **keywords** and critical emphasis (configurable but coral is default)

---

## 6. WOW Visualization Enhancements (3 Features)

> These three features must exist across **all** modules and be consistent with the WOW UI theme/language/style.

### 6.1 WOW Interactive Indicator (Enhanced)
A persistent indicator component representing:
- overall session state: idle / running / blocked / error / success
- module statuses: Guidance Workspace, Guidance Generator (Step 3), Agent Studio, Note Keeper, 510(k) tools
- active provider/model selection and key readiness state

**Interactive behaviors**
- Clicking the indicator opens a **Run Inspector Drawer**:
  - current run step (e.g., “Agent 3/7: Deficiency Extractor”)
  - elapsed time, retries (if any), and throttling notes
  - “What is happening?” human-readable explanation localized to UI language
  - immediate actions:
    - cancel run (best-effort)
    - copy run prompt (masked if contains secrets; should not)
    - open Live Log filtered to this run

**Status semantics**
- **Blocked**: preflight failed (missing key, missing input pages, invalid model)
- **Running**: LLM call in progress
- **Done**: successful completion + artifact saved
- **Warning**: completed but constraint checks failed (e.g., table count mismatch)
- **Error**: exception occurred; shows friendly summary + technical detail accordion

### 6.2 Live Log (Enhanced, Streaming-First)
A dedicated panel/tab providing:
- streaming run events (structured), appended in real time
- filters and search
- export to `.jsonl` and `.txt` (user-initiated)

**Event schema (minimum fields)**
- timestamp (UTC + local)
- run_id (UUID-like)
- module (Guidance/OCR/Step3/AgentStudio/NoteKeeper/510k)
- severity (info/warn/error)
- event_type (preflight, request_sent, partial_received, completed, retry, blocked, exception)
- provider + model
- input size estimates (chars/pages)
- output size estimates (chars)
- token/cost estimates (if available)
- latency metrics (queue time, generation time)

**UX details**
- Two modes:
  - **Simple**: readable narrative log (“Step 3 started… received output…”)
  - **Technical**: shows structured JSON fields
- One-click actions:
  - “Filter to current run”
  - “Copy error summary”
  - “Open artifact created by this event” (if available)
- Privacy guarantees:
  - never log API keys
  - redact any detected secret-like patterns in prompts (best-effort)

### 6.3 WOW Interactive Dashboard (Enhanced)
A central observability and productivity hub.

**Core widgets**
1. **Run Timeline** (interactive)
   - shows each run as a segment with start/end and status
   - click a segment → open Run Inspector with prompt pin, model, artifacts, logs
2. **Model Mix & Provider Mix**
   - donut/bar charts showing usage by model/provider within session
3. **Token/Cost Estimator Panel (best-effort)**
   - displays rough token estimate from input/output size
   - shows user-facing disclaimers (“estimates only”)
4. **Bottleneck Analyzer**
   - highlights slowest steps and likely causes (OCR page count, huge prompts, model choice)
5. **Constraint Compliance Monitor**
   - tracks Step 3 constraints: word count estimate + table count estimate
   - shows how many runs passed/failed constraints
6. **Artifact Quick Access**
   - latest Guidance Markdown
   - latest Agent output
   - latest Note Keeper organized note
   - download shortcuts

**Interactivity requirements**
- cross-filtering: selecting a model updates the timeline to highlight runs with that model
- deep-link behavior: dashboard → opens relevant module at the correct step with artifacts loaded in view

---

## 7. API Key Management (Environment-First, UI Fallback)

### 7.1 Key Sources and Priority
1. **Environment secrets** (Hugging Face Space secrets)
2. **User-provided UI key** (session-only)

### 7.2 UI Requirements
- If environment key exists for a provider:
  - show status: “Managed by environment”
  - show a green readiness indicator
  - do **not** show the key, not even partially
  - optional: show last-4 hash fingerprint **only if derived safely** (no reversible display), otherwise omit
- If environment key is missing:
  - show a password input box for user entry
  - show a “store only in this session” label
  - show “clear key” action

### 7.3 Preflight Blocking (Consistency Rule)
Before any LLM call:
- determine provider from selected model
- confirm provider key exists (env or session)
- if missing: set status to **Blocked**, log a structured preflight event, and show a clear localized message:
  - what is missing (which provider key)
  - how to fix (enter key or set Space secret)
  - suggest a model/provider that is available

---

## 8. Multi-Provider Model Selection (Standardized)

### 8.1 Global Model Allowlist (UI)
The model dropdowns across modules must include, at minimum:

**OpenAI**
- `gpt-4o-mini`
- `gpt-4.1-mini`

**Gemini**
- `gemini-2.5-flash`
- `gemini-3-flash-preview`

**Anthropic**
- “claude-*” models (configured list; examples):
  - `claude-3.5-sonnet`
  - `claude-3.5-haiku`

**Grok/xAI**
- `grok-4-fast-reasoning`
- `grok-3-mini`

### 8.2 Module-Specific Allowlists
Some modules may restrict to subsets (performance/cost/format reliability). Example:
- Gemini Vision OCR: Gemini models only
- Step 3 Guidance Generator: allow OpenAI + Gemini by default, optionally include Anthropic/Grok if validated for table constraints

---

## 9. Guidance OCR & Generator Module (Retained + Strengthened)

### 9.1 Step 1 — Ingest Guidance
Inputs:
- paste TXT/Markdown
- upload `.txt`, `.md`, `.pdf`

Rules:
- if both paste and file exist, user selects which to use (explicit toggle recommended to avoid surprises)
- normalize line endings; preserve headings and bullets

### 9.2 Step 1b — PDF Preview & Page Selection
- inline PDF preview
- show page count
- multi-select pages
- guardrails:
  - default selection limited (e.g., first 3–5 pages)
  - warnings when selecting large page ranges
  - show “estimated OCR time/cost” if possible

### 9.3 Step 2 — Extraction / OCR
Modes:
1. **Python extraction** via `pypdf` (fast; best for digital PDFs)
2. **Python OCR** (optional): render pages + `pytesseract` (depends on runtime)
3. **LLM OCR (Gemini Vision)**: render pages to images and transcribe

Requirements:
- create merged raw guidance text with page delimiters
- generate OCR diagnostics per page (chars extracted, OCR method used, warnings)

Safety limits:
- max pages per run (configurable; default recommended)
- visible progress via WOW indicator + Live Log events

### 9.4 Step 3 — Generate Organized Guidance Markdown (2000–3000 words; exactly 3 tables)
**Purpose:** produce a reviewer-friendly structured guidance document.

Inputs:
- raw guidance text
- output language toggle (English / Traditional Chinese)
- editable prompt
- model selection (OpenAI/Gemini + others if enabled)
- parameters: max tokens, temperature

Hard constraints enforced by prompt contract:
- 2000–3000 words (note: heuristic for CJK; UI labels it as an estimate)
- exactly **3 Markdown tables** in the entire document
- no hallucinated requirements; if uncertain, explicitly state uncertainty and recommend verification
- structured headings for reviewer use (scope, key review points, evidence expectations, common deficiencies, etc.)

**Compliance checks (post-generation, heuristic)**
- word count estimate
- table count estimate (regex-based)
- show pass/warn status; warn triggers “Regenerate with constraints” option (design-level)

Outputs:
- `guidance_doc_md`
- pinned prompt snapshot used
- run metadata for dashboard/log

### 9.5 Step 4 — Edit & Download
- dual view: Markdown / plain text
- downloads: `.md` and `.txt`
- artifact versioning within session (keep last N versions)

---

## 10. Agent Studio (agents.yaml) — Editable, Stepwise Execution

### 10.1 Agent Definitions
Agents are loaded from `agents.yaml` with:
- name, description
- system prompt template
- user prompt template (parameterized)
- default model and parameter hints
- input/output artifact bindings

### 10.2 Pre-Run Controls (Per Agent)
Before running an agent, user can:
- select model (from allowlist)
- edit prompt content (system and/or user prompt depending on configuration)
- adjust max tokens and temperature
- choose input source artifact (e.g., guidance doc, previous agent output, pasted text)

Preflight checks:
- key availability for chosen model/provider
- input not empty
- length warnings (huge context → suggest trimming)

### 10.3 Post-Run Controls (Editable Output Chaining)
After execution:
- show output in:
  - Markdown view (rendered + source)
  - Text view
- user can edit output; edited output becomes the “effective output” artifact
- “Use as input to next agent” is explicit and visible
- store both:
  - raw model output (read-only)
  - user-edited effective output (used downstream)

### 10.4 Run Orchestration Modes
- **One-by-one (default)**: user manually runs each agent step
- Optional “guided run” mode (still stepwise): UI guides to next step but never auto-runs without confirmation

---

## 11. AI Note Keeper (Expanded) + AI Magics (Now 9)

### 11.1 Note Ingestion and Organization
User can paste:
- `.txt` content
- Markdown notes (messy or partial)

Primary “Organize Note” agent:
- transforms into structured Markdown:
  - title (if inferable)
  - sections with headings
  - bullet lists and action items
  - decision points and open questions
- extracts and highlights keywords in **coral color**
  - default: coral highlight via consistent Markdown/HTML styling approach supported by Streamlit rendering
  - user can customize keyword highlighting style (optional; coral remains default)

Editing:
- toggle Markdown view / TXT view
- edits update the effective note artifact

### 11.2 Prompt Pinning and Model Choice
- user can maintain a pinned “note transformation prompt”
- choose model per action (organize, refine, apply magic)
- provider-key preflight applies

### 11.3 AI Magics (Total 9)
The system retains the original 6 AI Magics and **adds 3 more**. Each magic:
- takes the effective note as input
- produces an editable Markdown output
- writes run metadata to dashboard/log
- is model-selectable

#### 11.3.1 Existing AI Magics (Retained, 6)
(These remain as originally designed; names may map to existing UI features.)
1. **Executive Summary Builder** (turn notes into brief + structured summary)
2. **Action Items Extractor** (tasks, owners placeholders, deadlines placeholders)
3. **Risk & Mitigation Draft** (identify risks; propose mitigations with uncertainty labels)
4. **Meeting Minutes Formatter** (attendees, agenda, decisions, next steps)
5. **Regulatory Checklist Generator** (convert notes into checklist rows)
6. **Keyword Highlighter/Refiner** (improve keyword selection; keep coral highlight)

#### 11.3.2 New AI Magics (Added in 4.2, 3)
7. **Traceability Matrix Builder (Notes → Evidence Map)**  
   Produces a Markdown table mapping:
   - note claim / requirement / question
   - suggested evidence type (test, document, standard, rationale)
   - status (unknown / needs confirmation / ready)
   - gaps and follow-ups  
   Includes explicit uncertainty tags and avoids fabricating evidence.

8. **Contradiction & Ambiguity Detector**  
   Scans notes to identify:
   - conflicting statements
   - ambiguous terms (e.g., “safe”, “validated”, “equivalent” without criteria)
   - missing definitions (device version, population, indications, endpoints)
   Outputs:
   - a list of issues
   - rewrite suggestions
   - “questions to ask” section for stakeholder follow-up

9. **Regulatory-Ready Rewrite (Localized Tone)**  
   Produces two parallel rewrites:
   - **Regulatory formal** (submission-ready tone)
   - **Internal actionable** (team-friendly tasks)  
   Respects the UI language toggle for labels and supports English/Traditional Chinese output selection. Adds a “Terminology normalization” section to standardize key device/regulatory terms.

---

## 12. 510(k) Intelligence, Comparator, and Report Tools (Preserved)

All existing 510(k) and report drafting tools remain in place. In 4.2 they inherit:
- WOW UI v2 theme/language/style
- consistent model selector and provider preflight
- Live Log events and Dashboard metrics
- optional Agent Studio chaining into/from 510(k) outputs

---

## 13. Reliability, Guardrails, and Error Handling

### 13.1 Common Failure Modes and Required Responses
- Missing key → block preflight; show fix instructions; log event
- Rate limit / quota → show provider-specific suggestion (retry later, switch model/provider)
- Oversized input → warn; suggest trimming pages or using summarization agent first
- OCR dependency missing → gracefully fallback (Python extraction or Gemini OCR) and explain in UI

### 13.2 Content Integrity Guardrails
- “Do not hallucinate” guidance included in system prompts for guidance generation and note transformations
- When source lacks details, model must:
  - state uncertainty
  - list what to verify

### 13.3 Constraint Compliance (Step 3)
- show compliance panel (word/table estimates)
- if failed:
  - status becomes Warning (not Error)
  - one-click “Regenerate with constraints” (design-level)
  - show targeted prompt hints (“avoid extra tables”)

---

## 14. Security, Privacy, and Data Handling

### 14.1 Data Handling Defaults
- session-state only storage
- no server-side persistence required
- user-initiated downloads only
- optional cache for performance (must not include keys)

### 14.2 Key Handling Guarantees
- never display environment keys
- never write keys to logs
- never persist UI-entered keys beyond session
- redact secret-like strings in Live Log (best-effort)

### 14.3 Hugging Face Spaces Considerations
- document clearly that Spaces runtime may restart, clearing session state
- recommend users download artifacts they care about

---

## 15. Deployment and Configuration

### 15.1 Required Files and Config
- Streamlit app entry
- `agents.yaml` shipped with default agents; optional user override upload
- `SKILL.md` for skill panel content
- environment secrets configured in Hugging Face Space:
  - `OPENAI_API_KEY`
  - `GEMINI_API_KEY` (or equivalent naming)
  - `ANTHROPIC_API_KEY`
  - `XAI_API_KEY` (or equivalent for Grok)

### 15.2 Operational Defaults
- conservative default max pages for OCR
- sensible default max tokens per module
- minimal telemetry: session-local only unless explicitly extended later

---

## 16. Acceptance Criteria (4.2)

1. Users can toggle **Light/Dark**, **English/Traditional Chinese**, and choose among **20 painter styles**; Jackpot random selection works.
2. WOW visualization features exist and are functional:
   - Interactive Indicator with drilldown
   - Live Log with filters/search/export
   - Interactive Dashboard with run timeline, model mix, token estimates, compliance monitor
3. API key UI:
   - shows input only when env key missing
   - never displays env key
   - UI key stored only in session
4. Agent Studio:
   - per-agent prompt/model/params editable before run
   - outputs editable after run and can be used as next input
5. AI Note Keeper:
   - organize note → Markdown with coral keywords
   - editable Markdown/TXT
   - 9 AI Magics available (6 original + 3 new)
6. System continues to run on Hugging Face Spaces using Streamlit, `agents.yaml`, and supports Gemini/OpenAI/Anthropic/Grok routing.

---

## 17. Follow-up Questions (20)

1. For the **20 painter styles**, do you want them to affect only colors/backgrounds, or also typography (e.g., serif vs sans), spacing density, and animation intensity?
2. Should the **Jackpot** selection re-roll on every page refresh, or remain stable for the whole session unless the user clicks Jackpot again?
3. Do you prefer that the **UI language toggle** changes only the interface, or should it also default the **generation language** for all modules unless overridden?
4. For Step 3’s “**2000–3000 words**” constraint, should Traditional Chinese be measured by estimated **word equivalents**, **character count**, or a dual metric displayed side-by-side?
5. Should the “**exactly 3 tables**” constraint apply strictly to *any* Markdown pipe table, or should HTML tables count too (and thus be disallowed)?
6. For **WOW Interactive Indicator**, do you want a single global indicator only, or separate mini-indicators embedded per module + a global summary?
7. Should the **Live Log** store only the current session, or also allow the user to download a “run bundle” containing logs + artifacts in a zip (user-initiated only)?
8. Do you want the **Dashboard** to estimate cost using configured per-model price tables, or show token counts only without any cost estimate?
9. For **token estimation**, should the app compute provider-specific tokenization estimates (more accurate) or use a simple chars→tokens heuristic (simpler, less accurate)?
10. In **Agent Studio**, should users be allowed to edit the **system prompt** for every agent, or only the **user prompt** by default with an “advanced” toggle?
11. Should agent chaining support **branching** (keeping multiple alternative outputs) or only a single linear “effective output” per agent?
12. Do you want an explicit **“diff viewer”** when a user edits an agent output (raw vs edited), to improve traceability?
13. For the **AI Note Keeper coral keyword highlight**, do you prefer inline highlighting (e.g., `<span style>`), or a separate “Keywords” section plus subtle inline emphasis for maximum Markdown portability?
14. Should the **Traceability Matrix Builder** magic (new) be allowed to create tables beyond Step 3 constraints (it’s a different module), or do you want a global “limit table creation” toggle?
15. For **Contradiction & Ambiguity Detector**, should it also output a list of **clarifying questions** formatted for email, meeting agenda, or Jira ticket creation?
16. For **Regulatory-Ready Rewrite (Localized Tone)**, should it generate bilingual output (EN + ZH) simultaneously, or only one selected language at a time?
17. Which **Anthropic models** should be explicitly listed in the UI (given account availability varies), and should the app allow a custom model name entry for Anthropic/Grok?
18. Do you want a **provider failover mode** (e.g., if OpenAI fails, retry once with Gemini) or should provider switching remain manual and explicit?
19. Should OCR support an additional “**auto-detect scanned pages**” heuristic (low extracted text triggers OCR suggestion), and how aggressive should it be?
20. Do you want the system to support **artifact persistence** across sessions (e.g., optional user download/upload bundles) while still avoiding any server-side storage?
