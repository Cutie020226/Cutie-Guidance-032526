from __future__ import annotations

import os
import io
import re
import json
import time
import base64
import uuid
import math
import datetime as dt
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

# Optional imports (graceful)
try:
    import yaml  # pyyaml
except Exception:
    yaml = None

try:
    import requests
except Exception:
    requests = None

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

try:
    import fitz  # pymupdf
except Exception:
    fitz = None

try:
    from PIL import Image
except Exception:
    Image = None

try:
    import pytesseract
except Exception:
    pytesseract = None

try:
    import altair as alt
except Exception:
    alt = None


# -----------------------------
# Constants & UI dictionaries
# -----------------------------

APP_NAME = "SmartMed Review 4.2"
APP_SUBTITLE = "智慧醫材審查指引與清單生成系統"
APP_VERSION = "4.2.0"

DEFAULT_MAX_TOKENS = 12000
DEFAULT_TEMPERATURE = 0.2

MODEL_CHOICES = [
    # OpenAI
    "gpt-4o-mini",
    "gpt-4.1-mini",
    # Gemini
    "gemini-2.5-flash",
    "gemini-3-flash-preview",
    # Anthropic (examples; adjust to your account availability)
    "claude-3.5-sonnet",
    "claude-3.5-haiku",
    # Grok/xAI
    "grok-4-fast-reasoning",
    "grok-3-mini",
]

STEP3_ALLOWED_MODELS = [
    "gpt-4o-mini",
    "gemini-2.5-flash",
    "gemini-3-flash-preview",
    # You may add others if you validate “exactly 3 tables” compliance
]

OCR_GEMINI_MODELS = ["gemini-2.5-flash", "gemini-3-flash-preview"]

PROVIDER_ENV_KEYS = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "grok": "XAI_API_KEY",  # adjust if you use a different env var
}

LANGS = ["English", "繁體中文"]

I18N = {
    "English": {
        "app_title": APP_NAME,
        "app_sub": "Comprehensive regulatory workspace (Streamlit on Hugging Face Spaces)",
        "settings": "Settings",
        "theme": "Theme",
        "language": "Language",
        "painter_style": "Painter Style",
        "jackpot": "Jackpot",
        "api_keys": "API Keys",
        "managed_env": "Managed by environment",
        "missing_key": "Missing key",
        "enter_key": "Enter API key (session only)",
        "clear_key": "Clear session key",
        "status": "Status",
        "dashboard": "WOW Dashboard",
        "guidance": "Guidance OCR & Generator",
        "agent_studio": "Agent Studio (agents.yaml)",
        "note_keeper": "AI Note Keeper",
        "live_log": "Live Log",
        "about": "About",
        "run": "Run",
        "run_next": "Run Next",
        "blocked": "Blocked",
        "running": "Running",
        "done": "Done",
        "warning": "Warning",
        "error": "Error",
        "export_log": "Export log",
        "download": "Download",
        "upload": "Upload",
        "paste": "Paste",
        "model": "Model",
        "max_tokens": "Max tokens",
        "temperature": "Temperature",
        "prompt": "Prompt",
        "system_prompt": "System prompt",
        "user_prompt": "User prompt",
        "input": "Input",
        "output": "Output",
        "markdown_view": "Markdown view",
        "text_view": "Text view",
        "preview": "Preview",
        "artifacts": "Artifacts",
        "preflight_failed": "Preflight failed",
        "fix_by_setting": "Fix by setting the provider API key (Space secret) or entering it in Settings.",
        "pdf_pages": "PDF pages",
        "select_pages": "Select pages (1-based)",
        "extract_mode": "Extraction / OCR mode",
        "mode_python_extract": "Python extract (pypdf)",
        "mode_python_ocr": "Python OCR (render + pytesseract)",
        "mode_gemini_ocr": "Gemini Vision OCR (render + Gemini)",
        "run_step3": "Generate organized guidance Markdown (Step 3)",
        "step3_constraints": "Constraints: 2000–3000 words (estimate), exactly 3 Markdown tables",
        "compliance": "Compliance Check (heuristic)",
        "word_est": "Word estimate",
        "cjk_char_count": "CJK character count",
        "table_count_est": "Table count estimate",
        "regenerate": "Regenerate with constraints",
        "agents_yaml": "agents.yaml",
        "upload_agents_yaml": "Upload agents.yaml (override session)",
        "load_default_agents": "Load default agents",
        "note_input": "Paste note (txt/markdown)",
        "organize_note": "Organize note → Markdown (coral keywords)",
        "ai_magic": "AI Magic",
        "apply_magic": "Apply Magic",
        "pin_prompt": "Pin prompt",
        "pinned_prompt": "Pinned prompt",
        "run_inspector": "Run Inspector",
        "filter": "Filter",
        "search": "Search",
        "clear_session": "Clear session",
    },
    "繁體中文": {
        "app_title": "SmartMed Review 4.2",
        "app_sub": "（Streamlit on Hugging Face Spaces）醫材法規審查工作台",
        "settings": "設定",
        "theme": "主題",
        "language": "語言",
        "painter_style": "畫家風格",
        "jackpot": "拉霸（隨機風格）",
        "api_keys": "API 金鑰",
        "managed_env": "由環境變數管理",
        "missing_key": "缺少金鑰",
        "enter_key": "輸入 API 金鑰（僅限本次 Session）",
        "clear_key": "清除 Session 金鑰",
        "status": "狀態",
        "dashboard": "WOW 儀表板",
        "guidance": "指引 OCR 與生成器",
        "agent_studio": "代理工作室（agents.yaml）",
        "note_keeper": "AI 筆記管家",
        "live_log": "即時日誌",
        "about": "關於",
        "run": "執行",
        "run_next": "執行下一步",
        "blocked": "被阻擋",
        "running": "執行中",
        "done": "完成",
        "warning": "警告",
        "error": "錯誤",
        "export_log": "匯出日誌",
        "download": "下載",
        "upload": "上傳",
        "paste": "貼上",
        "model": "模型",
        "max_tokens": "最大 tokens",
        "temperature": "溫度",
        "prompt": "提示詞",
        "system_prompt": "系統提示詞",
        "user_prompt": "使用者提示詞",
        "input": "輸入",
        "output": "輸出",
        "markdown_view": "Markdown 檢視",
        "text_view": "文字檢視",
        "preview": "預覽",
        "artifacts": "產物",
        "preflight_failed": "前置檢查失敗",
        "fix_by_setting": "請在 Space Secrets 設定金鑰，或至設定頁輸入（僅本次 Session）。",
        "pdf_pages": "PDF 頁面",
        "select_pages": "選擇頁碼（從 1 開始）",
        "extract_mode": "擷取 / OCR 模式",
        "mode_python_extract": "Python 擷取（pypdf）",
        "mode_python_ocr": "Python OCR（渲染 + pytesseract）",
        "mode_gemini_ocr": "Gemini Vision OCR（渲染 + Gemini）",
        "run_step3": "生成結構化指引 Markdown（Step 3）",
        "step3_constraints": "限制：2000–3000 words（估算），且全篇恰好 3 個 Markdown 表格",
        "compliance": "合規檢查（啟發式）",
        "word_est": "Words 估算",
        "cjk_char_count": "中日韓字元數",
        "table_count_est": "表格數估算",
        "regenerate": "依限制重新生成",
        "agents_yaml": "agents.yaml",
        "upload_agents_yaml": "上傳 agents.yaml（覆蓋本次 Session）",
        "load_default_agents": "載入預設 agents",
        "note_input": "貼上筆記（txt/markdown）",
        "organize_note": "整理筆記 → Markdown（珊瑚色關鍵字）",
        "ai_magic": "AI 魔法",
        "apply_magic": "套用魔法",
        "pin_prompt": "釘選提示詞",
        "pinned_prompt": "已釘選提示詞",
        "run_inspector": "執行檢視器",
        "filter": "篩選",
        "search": "搜尋",
        "clear_session": "清除 Session",
    },
}

PAINTER_STYLES = [
    "Monet", "Van Gogh", "Picasso", "Klimt", "Hokusai",
    "Rothko", "Pollock", "Vermeer", "Matisse", "Rembrandt",
    "Turner", "Cézanne", "Magritte", "Dalí", "Kandinsky",
    "Hopper", "O’Keeffe", "Basquiat", "Bruegel", "Ukiyo-e"
]

# Minimal style tokens per painter (extend as desired)
PAINTER_TOKENS = {
    "Monet":     {"accent": "#6EC6FF", "bg1": "#F7FBFF", "bg2": "#EAF4FF", "glow": "rgba(110,198,255,0.35)"},
    "Van Gogh":  {"accent": "#FFC857", "bg1": "#0B1F3A", "bg2": "#102B52", "glow": "rgba(255,200,87,0.35)"},
    "Picasso":   {"accent": "#FF6B6B", "bg1": "#FFF7F0", "bg2": "#F3F6FF", "glow": "rgba(255,107,107,0.25)"},
    "Klimt":     {"accent": "#D4AF37", "bg1": "#1B1A17", "bg2": "#26231C", "glow": "rgba(212,175,55,0.25)"},
    "Hokusai":   {"accent": "#1D4ED8", "bg1": "#F6FAFF", "bg2": "#E8F2FF", "glow": "rgba(29,78,216,0.25)"},
    "Rothko":    {"accent": "#C1121F", "bg1": "#FAF3F0", "bg2": "#F0E7E3", "glow": "rgba(193,18,31,0.2)"},
    "Pollock":   {"accent": "#22C55E", "bg1": "#0B0F14", "bg2": "#111827", "glow": "rgba(34,197,94,0.25)"},
    "Vermeer":   {"accent": "#3B82F6", "bg1": "#FFFDF8", "bg2": "#F3EFE5", "glow": "rgba(59,130,246,0.18)"},
    "Matisse":   {"accent": "#F97316", "bg1": "#FFF7ED", "bg2": "#FFEDD5", "glow": "rgba(249,115,22,0.22)"},
    "Rembrandt": {"accent": "#A16207", "bg1": "#121212", "bg2": "#1C1917", "glow": "rgba(161,98,7,0.25)"},
    "Turner":    {"accent": "#F59E0B", "bg1": "#FDF6E3", "bg2": "#FCE7C3", "glow": "rgba(245,158,11,0.2)"},
    "Cézanne":   {"accent": "#0EA5E9", "bg1": "#F0F9FF", "bg2": "#E0F2FE", "glow": "rgba(14,165,233,0.22)"},
    "Magritte":  {"accent": "#6366F1", "bg1": "#F5F3FF", "bg2": "#EDE9FE", "glow": "rgba(99,102,241,0.2)"},
    "Dalí":      {"accent": "#EC4899", "bg1": "#FFF1F2", "bg2": "#FFE4E6", "glow": "rgba(236,72,153,0.2)"},
    "Kandinsky": {"accent": "#14B8A6", "bg1": "#F0FDFA", "bg2": "#CCFBF1", "glow": "rgba(20,184,166,0.2)"},
    "Hopper":    {"accent": "#64748B", "bg1": "#F8FAFC", "bg2": "#EEF2F7", "glow": "rgba(100,116,139,0.2)"},
    "O’Keeffe":  {"accent": "#7C3AED", "bg1": "#FAF5FF", "bg2": "#F3E8FF", "glow": "rgba(124,58,237,0.2)"},
    "Basquiat":  {"accent": "#EF4444", "bg1": "#0A0A0A", "bg2": "#121212", "glow": "rgba(239,68,68,0.25)"},
    "Bruegel":   {"accent": "#16A34A", "bg1": "#FFFBEB", "bg2": "#FEF3C7", "glow": "rgba(22,163,74,0.18)"},
    "Ukiyo-e":   {"accent": "#0F766E", "bg1": "#F7FFFB", "bg2": "#DCFCE7", "glow": "rgba(15,118,110,0.18)"},
}

CORAL = "#FF7F50"


# -----------------------------
# Utility: run events & logging
# -----------------------------

@dataclass
class RunEvent:
    ts_utc: str
    run_id: str
    module: str
    severity: str          # info/warn/error
    event_type: str        # preflight/request_sent/partial_received/completed/retry/blocked/exception
    provider: str
    model: str
    message: str
    meta: Dict[str, Any]

def utc_now_iso() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def ensure_state():
    ss = st.session_state
    ss.setdefault("lang", "English")
    ss.setdefault("theme", "Light")
    ss.setdefault("painter_style", "Monet")
    ss.setdefault("jackpot_locked", True)

    ss.setdefault("session_keys", {"openai": None, "gemini": None, "anthropic": None, "grok": None})
    ss.setdefault("events", [])
    ss.setdefault("artifacts", {})
    ss.setdefault("active_run", None)   # dict with run metadata
    ss.setdefault("run_history", [])    # summarized runs

    ss.setdefault("agents_yaml_text", None)
    ss.setdefault("agents", None)
    ss.setdefault("agent_chain", {"index": 0, "effective_input": "", "outputs": []})

    ss.setdefault("guidance", {
        "raw_input": "",
        "pdf_bytes": None,
        "pdf_name": None,
        "page_count": 0,
        "selected_pages": [],
        "raw_text": "",
        "ocr_diagnostics": "",
        "step3_prompt": "",
        "step3_model": STEP3_ALLOWED_MODELS[0],
        "step3_output_md": "",
        "step3_output_effective": "",
        "step3_compliance": {},
    })

    ss.setdefault("note_keeper", {
        "note_input": "",
        "organized_md": "",
        "organized_effective": "",
        "pinned_prompt": "",
        "magic_output": "",
        "magic_effective": "",
    })

def t(key: str) -> str:
    lang = st.session_state.get("lang", "English")
    return I18N.get(lang, I18N["English"]).get(key, key)

def log_event(module: str, severity: str, event_type: str, provider: str, model: str, message: str, meta: Optional[Dict[str, Any]] = None, run_id: Optional[str] = None):
    if meta is None:
        meta = {}
    if run_id is None:
        run_id = st.session_state.get("active_run", {}).get("run_id", str(uuid.uuid4()))
    evt = RunEvent(
        ts_utc=utc_now_iso(),
        run_id=run_id,
        module=module,
        severity=severity,
        event_type=event_type,
        provider=provider,
        model=model,
        message=message,
        meta=meta,
    )
    st.session_state.events.append(asdict(evt))

def summarize_run(run_id: str, module: str, provider: str, model: str, status: str, meta: Dict[str, Any]):
    st.session_state.run_history.append({
        "ts_utc": utc_now_iso(),
        "run_id": run_id,
        "module": module,
        "provider": provider,
        "model": model,
        "status": status,
        **meta
    })


# -----------------------------
# Provider routing & key mgmt
# -----------------------------

def provider_from_model(model: str) -> str:
    m = (model or "").lower()
    if m.startswith("gpt-"):
        return "openai"
    if m.startswith("gemini-"):
        return "gemini"
    if m.startswith("claude-"):
        return "anthropic"
    if m.startswith("grok-"):
        return "grok"
    # fallback heuristic
    return "openai"

def get_key(provider: str) -> Tuple[Optional[str], str]:
    """Return (key, source) where source is 'env'|'session'|'missing'."""
    env_var = PROVIDER_ENV_KEYS.get(provider)
    if env_var:
        env_val = os.environ.get(env_var)
        if env_val:
            return env_val, "env"
    sess_val = st.session_state.session_keys.get(provider)
    if sess_val:
        return sess_val, "session"
    return None, "missing"

def preflight(provider: str, model: str, module: str, require_requests: bool = True) -> Tuple[bool, str]:
    if require_requests and requests is None:
        msg = "Dependency missing: requests"
        log_event(module, "error", "blocked", provider, model, msg, meta={"missing": "requests"})
        return False, msg
    key, src = get_key(provider)
    if not key:
        msg = f"{t('missing_key')}: {provider} ({PROVIDER_ENV_KEYS.get(provider, 'N/A')})"
        log_event(module, "warn", "blocked", provider, model, msg, meta={"source": src})
        return False, msg
    return True, "ok"

def safe_env_status(provider: str) -> str:
    key, src = get_key(provider)
    if src == "env":
        return t("managed_env")
    if src == "session":
        return "Session key set"
    return t("missing_key")

def redact_secrets(text: str) -> str:
    if not text:
        return text
    # Best-effort: redact common key patterns
    patterns = [
        r"sk-[A-Za-z0-9]{20,}",
        r"AIza[0-9A-Za-z\-_]{20,}",
        r"anthropic_[A-Za-z0-9]{20,}",
        r"xai-[A-Za-z0-9]{20,}",
    ]
    redacted = text
    for p in patterns:
        redacted = re.sub(p, "[REDACTED]", redacted)
    return redacted


# -----------------------------
# LLM Call (HTTP-first for portability)
# -----------------------------

def call_llm(provider: str, model: str, messages: List[Dict[str, str]], temperature: float, max_tokens: int, module: str, extra: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
    """
    Returns (text, meta). Uses HTTP calls for portability.
    - OpenAI: https://api.openai.com/v1/chat/completions
    - Grok (xAI): https://api.x.ai/v1/chat/completions (OpenAI-compatible)
    - Anthropic: https://api.anthropic.com/v1/messages
    - Gemini: uses google-generativeai if available; otherwise HTTP to generative language endpoint is not standardized here.
    """
    if extra is None:
        extra = {}

    ok, msg = preflight(provider, model, module, require_requests=(provider in ("openai", "anthropic", "grok")))
    if not ok:
        raise RuntimeError(msg)

    key, _ = get_key(provider)
    run_id = st.session_state.active_run["run_id"]
    log_event(module, "info", "request_sent", provider, model, "LLM request sent", meta={"max_tokens": max_tokens, "temperature": temperature, **extra}, run_id=run_id)

    t0 = time.time()
    text_out = ""
    meta_out: Dict[str, Any] = {"provider": provider, "model": model}

    if provider == "openai":
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": messages,
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
        }
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        if r.status_code >= 400:
            log_event(module, "error", "exception", provider, model, f"OpenAI error {r.status_code}", meta={"body": redact_secrets(r.text)}, run_id=run_id)
            raise RuntimeError(f"OpenAI API error {r.status_code}: {r.text[:4000]}")
        data = r.json()
        text_out = (data.get("choices", [{}])[0].get("message", {}) or {}).get("content", "") or ""
        meta_out.update({"usage": data.get("usage", {})})

    elif provider == "grok":
        url = "https://api.x.ai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": messages,
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
        }
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        if r.status_code >= 400:
            log_event(module, "error", "exception", provider, model, f"Grok error {r.status_code}", meta={"body": redact_secrets(r.text)}, run_id=run_id)
            raise RuntimeError(f"Grok API error {r.status_code}: {r.text[:4000]}")
        data = r.json()
        text_out = (data.get("choices", [{}])[0].get("message", {}) or {}).get("content", "") or ""
        meta_out.update({"usage": data.get("usage", {})})

    elif provider == "anthropic":
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        # Convert OpenAI-style messages to Anthropic-style
        system_text = ""
        anthropic_messages = []
        for m in messages:
            if m.get("role") == "system":
                system_text += (m.get("content") or "") + "\n"
            elif m.get("role") in ("user", "assistant"):
                anthropic_messages.append({"role": m["role"], "content": m.get("content") or ""})

        payload = {
            "model": model,
            "max_tokens": int(max_tokens),
            "temperature": float(temperature),
            "system": system_text.strip(),
            "messages": anthropic_messages,
        }
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        if r.status_code >= 400:
            log_event(module, "error", "exception", provider, model, f"Anthropic error {r.status_code}", meta={"body": redact_secrets(r.text)}, run_id=run_id)
            raise RuntimeError(f"Anthropic API error {r.status_code}: {r.text[:4000]}")
        data = r.json()
        content = data.get("content", [])
        if isinstance(content, list) and content:
            # typical: [{"type":"text","text":"..."}]
            text_out = "".join([c.get("text", "") for c in content if isinstance(c, dict)])
        else:
            text_out = ""
        meta_out.update({"usage": data.get("usage", {})})

    elif provider == "gemini":
        # Prefer google-generativeai library if present
        try:
            import google.generativeai as genai  # type: ignore
        except Exception:
            log_event(module, "error", "blocked", provider, model, "Gemini SDK missing: google-generativeai", meta={}, run_id=run_id)
            raise RuntimeError("Gemini SDK missing. Add google-generativeai to requirements.txt.")

        ok, msg = preflight("gemini", model, module, require_requests=False)
        if not ok:
            raise RuntimeError(msg)
        gkey, _ = get_key("gemini")
        genai.configure(api_key=gkey)

        # Flatten messages into a single prompt (Gemini accepts structured parts, but keep it simple)
        sys_parts = [m["content"] for m in messages if m.get("role") == "system"]
        user_parts = [m["content"] for m in messages if m.get("role") == "user"]
        assistant_parts = [m["content"] for m in messages if m.get("role") == "assistant"]

        prompt = ""
        if sys_parts:
            prompt += "SYSTEM:\n" + "\n".join(sys_parts).strip() + "\n\n"
        if assistant_parts:
            prompt += "ASSISTANT HISTORY:\n" + "\n".join(assistant_parts).strip() + "\n\n"
        prompt += "USER:\n" + "\n".join(user_parts).strip()

        gm = genai.GenerativeModel(model)
        resp = gm.generate_content(
            prompt,
            generation_config={
                "temperature": float(temperature),
                "max_output_tokens": int(max_tokens),
            },
        )
        text_out = getattr(resp, "text", "") or ""
        meta_out.update({"usage": getattr(resp, "usage_metadata", None)})

    else:
        raise RuntimeError(f"Unknown provider: {provider}")

    latency = time.time() - t0
    log_event(module, "info", "completed", provider, model, "LLM request completed", meta={"latency_s": round(latency, 3), "out_chars": len(text_out)}, run_id=run_id)
    return text_out, meta_out


# -----------------------------
# OCR & PDF helpers
# -----------------------------

def render_pdf_page_to_png_bytes(pdf_bytes: bytes, page_index0: int, zoom: float = 2.0) -> bytes:
    if fitz is None:
        raise RuntimeError("PyMuPDF (fitz) missing.")
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc.load_page(page_index0)
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    return pix.tobytes("png")

def pdf_text_extract_pypdf(pdf_bytes: bytes, page_indices0: List[int]) -> Tuple[str, str]:
    if PdfReader is None:
        raise RuntimeError("pypdf missing.")
    reader = PdfReader(io.BytesIO(pdf_bytes))
    diag_lines = []
    out_chunks = []
    for i0 in page_indices0:
        try:
            page = reader.pages[i0]
            txt = page.extract_text() or ""
            diag_lines.append(f"[Page {i0+1}] extracted_chars={len(txt)}")
            out_chunks.append(f"\n\n[PDF Page {i0+1}]\n{txt}".strip())
        except Exception as e:
            diag_lines.append(f"[Page {i0+1}] error={type(e).__name__}: {e}")
    return "\n".join(out_chunks).strip(), "\n".join(diag_lines).strip()

def python_ocr_pytesseract(pdf_bytes: bytes, page_indices0: List[int]) -> Tuple[str, str]:
    if fitz is None or Image is None or pytesseract is None:
        raise RuntimeError("Missing dependency for python OCR: fitz/PIL/pytesseract.")
    diag_lines = []
    out_chunks = []
    for i0 in page_indices0:
        try:
            png = render_pdf_page_to_png_bytes(pdf_bytes, i0, zoom=2.0)
            img = Image.open(io.BytesIO(png))
            txt = pytesseract.image_to_string(img)
            diag_lines.append(f"[Page {i0+1}] ocr_chars={len(txt)}")
            out_chunks.append(f"\n\n[PDF Page {i0+1}]\n{txt}".strip())
        except Exception as e:
            diag_lines.append(f"[Page {i0+1}] error={type(e).__name__}: {e}")
    return "\n".join(out_chunks).strip(), "\n".join(diag_lines).strip()

def gemini_vision_ocr(pdf_bytes: bytes, page_indices0: List[int], model: str) -> Tuple[str, str]:
    # Requires google-generativeai + fitz + PIL
    if fitz is None:
        raise RuntimeError("PyMuPDF (fitz) missing for Gemini Vision OCR.")
    try:
        import google.generativeai as genai  # type: ignore
    except Exception:
        raise RuntimeError("Gemini SDK missing. Add google-generativeai to requirements.txt.")

    ok, msg = preflight("gemini", model, module="OCR", require_requests=False)
    if not ok:
        raise RuntimeError(msg)
    gkey, _ = get_key("gemini")
    genai.configure(api_key=gkey)

    prompt = (
        "You are an OCR transcription engine.\n"
        "Task: Faithfully transcribe the page image into text.\n"
        "Rules:\n"
        "- Preserve headings, bullets, numbering.\n"
        "- If you see a table, reconstruct as Markdown table when possible.\n"
        "- Do NOT hallucinate. If unreadable, mark as [UNREADABLE].\n"
        "- Avoid duplicating repeating headers/footers if clearly repetitive.\n"
    )

    diag_lines = []
    out_chunks = []
    gm = genai.GenerativeModel(model)

    for i0 in page_indices0:
        try:
            png = render_pdf_page_to_png_bytes(pdf_bytes, i0, zoom=2.0)
            # google-generativeai supports "inline_data"
            resp = gm.generate_content(
                [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/png", "data": base64.b64encode(png).decode("utf-8")}},
                ],
                generation_config={"temperature": 0.0, "max_output_tokens": 4096},
            )
            txt = getattr(resp, "text", "") or ""
            diag_lines.append(f"[Page {i0+1}] gemini_ocr_chars={len(txt)}")
            out_chunks.append(f"\n\n[PDF Page {i0+1}]\n{txt}".strip())
        except Exception as e:
            diag_lines.append(f"[Page {i0+1}] error={type(e).__name__}: {e}")

    return "\n".join(out_chunks).strip(), "\n".join(diag_lines).strip()

def embed_pdf_viewer(pdf_bytes: bytes, height: int = 500):
    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    pdf_html = f"""
    <iframe
        src="data:application/pdf;base64,{b64}"
        width="100%"
        height="{height}"
        style="border: 1px solid rgba(127,127,127,0.25); border-radius: 12px;"
    ></iframe>
    """
    st.components.v1.html(pdf_html, height=height+20)


# -----------------------------
# Step 3 compliance heuristics
# -----------------------------

_CJK_RE = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")

def estimate_words(text: str) -> int:
    if not text:
        return 0
    # Simple heuristic: split on whitespace for non-CJK
    tokens = re.findall(r"\b\w+\b", text)
    return len(tokens)

def count_cjk_chars(text: str) -> int:
    if not text:
        return 0
    return len(_CJK_RE.findall(text))

def estimate_table_blocks(md: str) -> int:
    """
    Heuristic: count Markdown table blocks by detecting header separator lines:
    e.g. | a | b |
         |---|---|
    """
    if not md:
        return 0
    lines = md.splitlines()
    count = 0
    i = 0
    while i < len(lines) - 1:
        line = lines[i].strip()
        nxt = lines[i+1].strip()
        is_row = line.startswith("|") and line.endswith("|") and ("|" in line[1:-1])
        is_sep = bool(re.match(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$", nxt))
        if is_row and is_sep:
            count += 1
            # skip forward until blank line or non-table row
            j = i + 2
            while j < len(lines):
                l = lines[j].strip()
                if not l:
                    break
                if not (l.startswith("|") and l.endswith("|")):
                    break
                j += 1
            i = j
        else:
            i += 1
    return count

def compute_step3_compliance(md: str) -> Dict[str, Any]:
    return {
        "word_estimate": estimate_words(md),
        "cjk_char_count": count_cjk_chars(md),
        "table_count_estimate": estimate_table_blocks(md),
    }


# -----------------------------
# Agents.yaml loader (with fallback)
# -----------------------------

DEFAULT_AGENTS_YAML = """
agents:
  - id: A1
    name: Guidance Summarizer
    description: Summarize guidance into key sections for reviewers.
    system_prompt: |
      You are a medical device regulatory assistant. Do not hallucinate.
    user_prompt: |
      Summarize the input into: Scope, Key Review Points, Evidence Expectations, Common Deficiencies.
      Input:
      {{input}}
    default_model: gemini-2.5-flash

  - id: A2
    name: Checklist Builder
    description: Convert summarized guidance into a checklist table plus narrative.
    system_prompt: |
      You are a medical device regulatory assistant. Do not hallucinate.
    user_prompt: |
      Create a reviewer checklist in Markdown (use ONE table) and a short narrative.
      Input:
      {{input}}
    default_model: gpt-4o-mini

  - id: A3
    name: Deficiency Letter Draft
    description: Draft deficiency questions based on gaps.
    system_prompt: |
      You are a medical device regulatory reviewer. Be precise and non-hallucinatory.
    user_prompt: |
      Draft deficiency questions. If uncertain, ask for confirmation.
      Input:
      {{input}}
    default_model: claude-3.5-haiku
"""

def load_agents(yaml_text: str) -> List[Dict[str, Any]]:
    if yaml is None:
        raise RuntimeError("pyyaml missing. Add pyyaml to requirements.txt.")
    obj = yaml.safe_load(yaml_text) or {}
    agents = obj.get("agents", [])
    if not isinstance(agents, list):
        raise RuntimeError("Invalid agents.yaml: 'agents' must be a list.")
    norm = []
    for a in agents:
        if not isinstance(a, dict):
            continue
        norm.append({
            "id": a.get("id") or str(uuid.uuid4())[:8],
            "name": a.get("name") or "Unnamed agent",
            "description": a.get("description") or "",
            "system_prompt": a.get("system_prompt") or "",
            "user_prompt": a.get("user_prompt") or "",
            "default_model": a.get("default_model") or MODEL_CHOICES[0],
        })
    return norm


# -----------------------------
# WOW UI: CSS injection
# -----------------------------

def inject_wow_css(theme: str, painter: str):
    tok = PAINTER_TOKENS.get(painter, PAINTER_TOKENS["Monet"])
    accent = tok["accent"]
    bg1 = tok["bg1"]
    bg2 = tok["bg2"]
    glow = tok["glow"]
    is_dark = (theme.lower() == "dark")

    # Streamlit theming is limited; we apply scoped CSS for panels and badges.
    css = f"""
    <style>
      :root {{
        --wow-accent: {accent};
        --wow-coral: {CORAL};
        --wow-bg1: {bg1};
        --wow-bg2: {bg2};
        --wow-glow: {glow};
        --wow-text: {"#E5E7EB" if is_dark else "#0F172A"};
        --wow-surface: {"rgba(17,24,39,0.75)" if is_dark else "rgba(255,255,255,0.75)"};
        --wow-border: {"rgba(148,163,184,0.18)" if is_dark else "rgba(15,23,42,0.12)"};
      }}

      .stApp {{
        background: radial-gradient(1200px 600px at 20% 10%, var(--wow-bg2), transparent 60%),
                    radial-gradient(1000px 600px at 80% 0%, var(--wow-bg1), transparent 55%),
                    linear-gradient(180deg, var(--wow-bg1), var(--wow-bg2));
        color: var(--wow-text);
      }}

      .wow-card {{
        background: var(--wow-surface);
        border: 1px solid var(--wow-border);
        box-shadow: 0 10px 30px rgba(0,0,0,0.10);
        border-radius: 16px;
        padding: 14px 16px;
        margin: 8px 0;
      }}

      .wow-badge {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        border-radius: 999px;
        padding: 6px 10px;
        border: 1px solid var(--wow-border);
        background: rgba(0,0,0,0.04);
      }}

      .wow-dot {{
        width: 10px;
        height: 10px;
        border-radius: 999px;
        background: var(--wow-accent);
        box-shadow: 0 0 0 0 var(--wow-glow);
        animation: wowPulse 1.6s infinite;
      }}

      @keyframes wowPulse {{
        0% {{ box-shadow: 0 0 0 0 var(--wow-glow); }}
        70% {{ box-shadow: 0 0 0 10px rgba(0,0,0,0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(0,0,0,0); }}
      }}

      .wow-coral {{ color: var(--wow-coral); font-weight: 600; }}

      .wow-kv {{
        display: grid;
        grid-template-columns: 140px 1fr;
        gap: 8px 12px;
        font-size: 0.95rem;
      }}

      .wow-kv .k {{ opacity: 0.75; }}
      .wow-kv .v {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}

      /* Make code blocks feel nicer */
      pre {{
        border-radius: 14px !important;
        border: 1px solid var(--wow-border) !important;
      }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# -----------------------------
# WOW components
# -----------------------------

def set_active_run(module: str, provider: str, model: str) -> str:
    run_id = str(uuid.uuid4())
    st.session_state.active_run = {
        "run_id": run_id,
        "module": module,
        "provider": provider,
        "model": model,
        "status": "running",
        "started_ts_utc": utc_now_iso(),
        "started_epoch": time.time(),
    }
    log_event(module, "info", "preflight", provider, model, "Run started", meta={}, run_id=run_id)
    return run_id

def finish_active_run(status: str, meta: Optional[Dict[str, Any]] = None):
    if meta is None:
        meta = {}
    ar = st.session_state.get("active_run")
    if not ar:
        return
    ar["status"] = status
    ar["ended_ts_utc"] = utc_now_iso()
    ar["latency_s"] = round(time.time() - ar.get("started_epoch", time.time()), 3)
    summarize_run(ar["run_id"], ar["module"], ar["provider"], ar["model"], status, meta)
    st.session_state.active_run = None

def wow_indicator():
    ar = st.session_state.get("active_run")
    if ar:
        status = t("running")
        dot_color = "var(--wow-accent)"
        subtitle = f"{ar['module']} • {ar['model']}"
    else:
        status = "Idle"
        dot_color = "var(--wow-accent)"
        subtitle = f"{st.session_state.theme} • {st.session_state.painter_style}"

    st.markdown(
        f"""
        <div class="wow-card">
          <div style="display:flex; align-items:center; justify-content:space-between; gap:12px;">
            <div class="wow-badge">
              <span class="wow-dot" style="background:{dot_color};"></span>
              <span><b>{t("status")}:</b> {status}</span>
            </div>
            <div style="opacity:0.8;">{subtitle}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander(t("run_inspector"), expanded=False):
        if ar:
            st.markdown("**Run ID**: `" + ar["run_id"] + "`")
            st.markdown("**Module**: " + ar["module"])
            st.markdown("**Model**: `" + ar["model"] + "`")
            st.markdown("**Started (UTC)**: " + ar["started_ts_utc"])
            st.markdown("**Elapsed (s)**: " + str(round(time.time() - ar.get("started_epoch", time.time()), 3)))
            st.caption("Open Live Log and filter by this run_id for details.")
        else:
            st.caption("No active run. Use the Live Log to inspect completed runs.")


# -----------------------------
# Sidebar: global settings & keys
# -----------------------------

def sidebar_settings():
    st.sidebar.markdown(f"## {t('settings')}")
    st.sidebar.caption(f"{APP_NAME} • v{APP_VERSION}")

    # Theme & language
    st.session_state.theme = st.sidebar.selectbox(t("theme"), ["Light", "Dark"], index=0 if st.session_state.theme == "Light" else 1)
    st.session_state.lang = st.sidebar.selectbox(t("language"), LANGS, index=LANGS.index(st.session_state.lang))

    # Painter style + Jackpot
    colA, colB = st.sidebar.columns([3, 2])
    with colA:
        st.session_state.painter_style = st.selectbox(t("painter_style"), PAINTER_STYLES, index=PAINTER_STYLES.index(st.session_state.painter_style))
    with colB:
        if st.button(t("jackpot")):
            # Re-roll style
            st.session_state.painter_style = PAINTER_STYLES[int(time.time()) % len(PAINTER_STYLES)]

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### {t('api_keys')}")

    for provider in ["openai", "gemini", "anthropic", "grok"]:
        env_var = PROVIDER_ENV_KEYS.get(provider, "")
        key, src = get_key(provider)
        st.sidebar.markdown(f"**{provider.upper()}**")
        st.sidebar.caption(f"Env: `{env_var}` • {safe_env_status(provider)}")
        if src != "env":
            new_key = st.sidebar.text_input(t("enter_key"), type="password", key=f"key_in_{provider}")
            cols = st.sidebar.columns([1, 1])
            with cols[0]:
                if st.button(t("run") + " preflight", key=f"preflight_{provider}"):
                    # dry validation
                    if new_key:
                        st.session_state.session_keys[provider] = new_key
                    ok, msg = preflight(provider, MODEL_CHOICES[0], module="Settings", require_requests=(provider in ("openai", "anthropic", "grok")))
                    st.sidebar.success("OK" if ok else msg)
            with cols[1]:
                if st.button(t("clear_key"), key=f"clear_{provider}"):
                    st.session_state.session_keys[provider] = None
                    st.rerun()
        st.sidebar.markdown("")

    st.sidebar.markdown("---")
    if st.sidebar.button(t("clear_session")):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# -----------------------------
# Module: Dashboard (WOW Interactive Dashboard)
# -----------------------------

def dashboard_tab():
    st.markdown(f"## {t('dashboard')}")
    wow_indicator()

    # Summary cards
    runs = st.session_state.run_history
    total = len(runs)
    by_status = {}
    by_model = {}
    by_module = {}
    for r in runs:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
        by_model[r["model"]] = by_model.get(r["model"], 0) + 1
        by_module[r["module"]] = by_module.get(r["module"], 0) + 1

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total runs", total)
    c2.metric("Done", by_status.get("done", 0))
    c3.metric("Warnings", by_status.get("warning", 0))
    c4.metric("Errors", by_status.get("error", 0))

    st.markdown("### Run Timeline")
    if runs:
        st.dataframe(runs[-30:][::-1], use_container_width=True, hide_index=True)
    else:
        st.caption("No runs yet. Execute guidance generation, agents, or note magics to populate.")

    st.markdown("### Model Mix")
    if by_model:
        st.dataframe([{"model": k, "count": v} for k, v in sorted(by_model.items(), key=lambda x: -x[1])],
                     use_container_width=True, hide_index=True)
    else:
        st.caption("No model usage recorded.")

    st.markdown("### Constraint Compliance Monitor (Step 3)")
    comp = st.session_state.guidance.get("step3_compliance") or {}
    if st.session_state.guidance.get("step3_output_md"):
        st.markdown(
            f"""
            <div class="wow-card">
              <div class="wow-kv">
                <div class="k">{t('word_est')}</div><div class="v">{comp.get('word_estimate', '')}</div>
                <div class="k">{t('cjk_char_count')}</div><div class="v">{comp.get('cjk_char_count', '')}</div>
                <div class="k">{t('table_count_est')}</div><div class="v">{comp.get('table_count_estimate', '')}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.caption("Generate Step 3 output to see compliance checks.")

    st.markdown("### Artifact Quick Access")
    a = st.session_state.artifacts
    if a:
        for k in sorted(a.keys()):
            with st.expander(k, expanded=False):
                v = a[k]
                if isinstance(v, str) and len(v) < 20000:
                    st.code(v, language="markdown")
                else:
                    st.caption("Artifact is large or non-text.")
    else:
        st.caption("No artifacts saved yet.")


# -----------------------------
# Module: Guidance OCR & Generator
# -----------------------------

def guidance_tab():
    st.markdown(f"## {t('guidance')}")
    wow_indicator()

    g = st.session_state.guidance

    st.markdown("### Step 1 — Ingest Guidance (Paste or Upload)")
    col1, col2 = st.columns([2, 1])

    with col1:
        g["raw_input"] = st.text_area(t("paste"), value=g.get("raw_input", ""), height=160, placeholder="Paste guidance text or markdown here...")

    with col2:
        upl = st.file_uploader(t("upload"), type=["pdf", "txt", "md"], key="guidance_upload")
        if upl is not None:
            if upl.type == "application/pdf" or upl.name.lower().endswith(".pdf"):
                g["pdf_bytes"] = upl.read()
                g["pdf_name"] = upl.name
                # page count
                if fitz is not None:
                    try:
                        doc = fitz.open(stream=g["pdf_bytes"], filetype="pdf")
                        g["page_count"] = doc.page_count
                    except Exception:
                        g["page_count"] = 0
                elif PdfReader is not None:
                    try:
                        reader = PdfReader(io.BytesIO(g["pdf_bytes"]))
                        g["page_count"] = len(reader.pages)
                    except Exception:
                        g["page_count"] = 0
            else:
                # txt/md
                txt = upl.read().decode("utf-8", errors="ignore")
                g["raw_input"] = txt

    if g.get("pdf_bytes"):
        st.markdown("### Step 1b — PDF Preview + Page Selection")
        st.caption(f"File: {g.get('pdf_name')} • pages: {g.get('page_count', 0)}")
        try:
            embed_pdf_viewer(g["pdf_bytes"], height=520)
        except Exception as e:
            st.warning(f"PDF preview unavailable: {e}")

        page_count = int(g.get("page_count") or 0)
        default_pages = list(range(1, min(5, page_count) + 1)) if page_count > 0 else []
        selected = st.multiselect(
            t("select_pages"),
            options=list(range(1, page_count + 1)) if page_count > 0 else [],
            default=g.get("selected_pages") or default_pages,
        )
        g["selected_pages"] = selected

        st.markdown("### Step 2 — Extraction / OCR")
        mode = st.radio(
            t("extract_mode"),
            [t("mode_python_extract"), t("mode_python_ocr"), t("mode_gemini_ocr")],
            index=0,
        )

        ocr_model = None
        if mode == t("mode_gemini_ocr"):
            ocr_model = st.selectbox(t("model"), OCR_GEMINI_MODELS, index=0)

        if st.button(t("run") + " Step 2", type="primary"):
            page_indices0 = [p - 1 for p in (g.get("selected_pages") or [])]
            if not page_indices0:
                st.warning("No pages selected.")
            else:
                try:
                    module = "Guidance/OCR"
                    model = ocr_model or "n/a"
                    provider = provider_from_model(model) if ocr_model else "n/a"
                    rid = set_active_run(module, provider, model)

                    raw_text = ""
                    diag = ""
                    if mode == t("mode_python_extract"):
                        raw_text, diag = pdf_text_extract_pypdf(g["pdf_bytes"], page_indices0)
                    elif mode == t("mode_python_ocr"):
                        raw_text, diag = python_ocr_pytesseract(g["pdf_bytes"], page_indices0)
                    else:
                        raw_text, diag = gemini_vision_ocr(g["pdf_bytes"], page_indices0, ocr_model)

                    g["raw_text"] = raw_text
                    g["ocr_diagnostics"] = diag
                    st.session_state.artifacts["guidance_raw_text"] = raw_text
                    st.session_state.artifacts["ocr_diagnostics"] = diag
                    finish_active_run("done", {"pages": len(page_indices0), "out_chars": len(raw_text)})
                    st.success("Step 2 completed.")
                except Exception as e:
                    log_event("Guidance/OCR", "error", "exception", provider if 'provider' in locals() else "n/a", model if 'model' in locals() else "n/a", str(e), meta={}, run_id=st.session_state.get("active_run", {}).get("run_id", str(uuid.uuid4())))
                    finish_active_run("error", {"error": str(e)})
                    st.error(f"Step 2 failed: {e}")

        with st.expander("Raw text & OCR diagnostics", expanded=False):
            st.text_area("Raw extracted/OCR text", value=g.get("raw_text", ""), height=220)
            st.text_area("Diagnostics", value=g.get("ocr_diagnostics", ""), height=140)

    st.markdown("### Step 3 — Organized Guidance Markdown Generator")
    st.caption(t("step3_constraints"))

    # Input for Step 3: prefer raw_text from PDF extraction, else pasted raw_input
    raw_for_step3 = (g.get("raw_text") or "").strip() or (g.get("raw_input") or "").strip()

    colA, colB, colC = st.columns([2, 1, 1])
    with colA:
        g["step3_model"] = st.selectbox(t("model"), STEP3_ALLOWED_MODELS, index=STEP3_ALLOWED_MODELS.index(g.get("step3_model") or STEP3_ALLOWED_MODELS[0]))
    with colB:
        max_tokens = st.number_input(t("max_tokens"), min_value=512, max_value=32000, value=int(g.get("step3_max_tokens") or DEFAULT_MAX_TOKENS), step=256)
        g["step3_max_tokens"] = int(max_tokens)
    with colC:
        temp = st.slider(t("temperature"), 0.0, 1.0, float(g.get("step3_temperature") or DEFAULT_TEMPERATURE), 0.05)
        g["step3_temperature"] = float(temp)

    default_step3_prompt = (
        "Transform the provided medical device guidance into a reviewer-friendly organized Markdown document.\n"
        "HARD CONSTRAINTS:\n"
        "1) Length: 2000–3000 words (estimate).\n"
        "2) Exactly 3 Markdown tables in the entire document (no more, no less).\n"
        "3) Do NOT hallucinate requirements. If source lacks details, clearly mark uncertainty and suggest what to confirm.\n"
        "STRUCTURE:\n"
        "- Title\n"
        "- Scope & applicability\n"
        "- Key review points\n"
        "- Evidence expectations\n"
        "- Common deficiencies\n"
        "- Risk considerations\n"
        "TABLES (exactly 3):\n"
        "- Table 1: Reviewer checklist\n"
        "- Table 2: Common deficiencies → risks → recommended evidence\n"
        "- Table 3: Standards/requirements mapping (only if present; otherwise a “to confirm” mapping)\n"
        "Output in the selected language.\n"
    )

    g["step3_prompt"] = st.text_area(t("prompt"), value=g.get("step3_prompt") or default_step3_prompt, height=200)

    lang_out = st.selectbox("Output language (content)", ["English", "繁體中文"], index=0 if st.session_state.lang == "English" else 1)

    colRun, colRegen = st.columns([1, 1])
    with colRun:
        if st.button(t("run_step3"), type="primary", disabled=(not raw_for_step3)):
            model = g["step3_model"]
            provider = provider_from_model(model)
            module = "Guidance/Step3"

            # Preflight (block before running)
            ok, msg = preflight(provider, model, module, require_requests=(provider in ("openai", "anthropic", "grok")))
            if not ok:
                st.warning(f"{t('preflight_failed')}: {msg}\n\n{t('fix_by_setting')}")
                log_event(module, "warn", "blocked", provider, model, msg, meta={"reason": "missing_key_or_dependency"})
                finish_active_run("warning", {"blocked": True})
            else:
                try:
                    rid = set_active_run(module, provider, model)
                    sys_prompt = "You are a meticulous medical device regulatory assistant. Follow constraints exactly."
                    user_prompt = (
                        f"{g['step3_prompt'].strip()}\n\n"
                        f"SELECTED LANGUAGE: {lang_out}\n\n"
                        f"SOURCE TEXT:\n{raw_for_step3}"
                    )
                    messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}]
                    out, meta = call_llm(provider, model, messages, temperature=g["step3_temperature"], max_tokens=g["step3_max_tokens"], module=module,
                                         extra={"input_chars": len(raw_for_step3), "lang_out": lang_out})
                    g["step3_output_md"] = out
                    g["step3_output_effective"] = out
                    comp = compute_step3_compliance(out)
                    g["step3_compliance"] = comp
                    st.session_state.artifacts["guidance_doc_md"] = out
                    st.session_state.artifacts["guidance_step3_prompt_pinned"] = user_prompt
                    status = "done"
                    # If table count != 3, mark warning
                    if comp.get("table_count_estimate") != 3:
                        status = "warning"
                    finish_active_run(status, {"word_est": comp.get("word_estimate"), "tables_est": comp.get("table_count_estimate")})
                    st.success("Step 3 completed." if status == "done" else "Step 3 completed with warnings (constraint mismatch).")
                except Exception as e:
                    log_event(module, "error", "exception", provider, model, str(e), meta={}, run_id=st.session_state.get("active_run", {}).get("run_id", str(uuid.uuid4())))
                    finish_active_run("error", {"error": str(e)})
                    st.error(f"Step 3 failed: {e}")

    with colRegen:
        if st.button(t("regenerate"), disabled=(not raw_for_step3)):
            # Slightly strengthen constraints automatically by appending a stricter reminder
            g["step3_prompt"] = (g.get("step3_prompt") or default_step3_prompt).strip() + (
                "\n\nSTRICT REMINDER:\n"
                "- Exactly 3 Markdown tables total. Do not add any other tables.\n"
                "- Avoid table-like formatting elsewhere.\n"
                "- If you already used 3 tables, do not create additional tables.\n"
            )
            st.info("Prompt strengthened. Click Step 3 Run again.")

    st.markdown("### Step 3 Output (Editable → Effective Artifact)")
    view_mode = st.radio("View", [t("markdown_view"), t("text_view")], horizontal=True)
    effective = st.text_area(t("output"), value=g.get("step3_output_effective", ""), height=300, key="step3_effective_edit")
    g["step3_output_effective"] = effective
    st.session_state.artifacts["guidance_doc_effective"] = effective

    if view_mode == t("markdown_view"):
        st.markdown("#### Preview")
        st.markdown(effective, unsafe_allow_html=True)

    st.markdown("### Downloads")
    if effective:
        st.download_button(
            label=f"{t('download')} .md",
            data=effective.encode("utf-8"),
            file_name="guidance_doc.md",
            mime="text/markdown",
        )
        st.download_button(
            label=f"{t('download')} .txt",
            data=effective.encode("utf-8"),
            file_name="guidance_doc.txt",
            mime="text/plain",
        )

    st.markdown("### Compliance Check (Heuristic)")
    comp = g.get("step3_compliance") or {}
    if comp:
        st.markdown(
            f"""
            <div class="wow-card">
              <div class="wow-kv">
                <div class="k">{t('word_est')}</div><div class="v">{comp.get('word_estimate', '')}</div>
                <div class="k">{t('cjk_char_count')}</div><div class="v">{comp.get('cjk_char_count', '')}</div>
                <div class="k">{t('table_count_est')}</div><div class="v">{comp.get('table_count_estimate', '')}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.caption("No compliance data yet.")


# -----------------------------
# Module: Agent Studio
# -----------------------------

def agent_studio_tab():
    st.markdown(f"## {t('agent_studio')}")
    wow_indicator()

    st.markdown("### Agents Source")
    colL, colR = st.columns([2, 1])
    with colL:
        st.caption("Load from default or upload an override. Loaded agents are session-only.")
    with colR:
        upl = st.file_uploader(t("upload_agents_yaml"), type=["yaml", "yml"], key="agents_yaml_upload")
        if upl is not None:
            st.session_state.agents_yaml_text = upl.read().decode("utf-8", errors="ignore")

    cols = st.columns([1, 1, 2])
    with cols[0]:
        if st.button(t("load_default_agents")):
            st.session_state.agents_yaml_text = DEFAULT_AGENTS_YAML
    with cols[1]:
        if st.button("Parse agents.yaml"):
            try:
                if not st.session_state.agents_yaml_text:
                    st.session_state.agents_yaml_text = DEFAULT_AGENTS_YAML
                st.session_state.agents = load_agents(st.session_state.agents_yaml_text)
                st.session_state.agent_chain = {"index": 0, "effective_input": st.session_state.artifacts.get("guidance_doc_effective", "") or "", "outputs": []}
                st.success(f"Loaded {len(st.session_state.agents)} agents.")
            except Exception as e:
                st.error(f"Failed to parse agents.yaml: {e}")

    with st.expander(t("agents_yaml"), expanded=False):
        st.code(st.session_state.agents_yaml_text or DEFAULT_AGENTS_YAML, language="yaml")

    agents = st.session_state.agents
    if not agents:
        st.info("No agents loaded yet. Click 'Load default agents' then 'Parse agents.yaml'.")
        return

    chain = st.session_state.agent_chain
    idx = int(chain.get("index", 0))
    idx = max(0, min(idx, len(agents) - 1))
    chain["index"] = idx

    st.markdown("### Chain Input (Editable)")
    chain_input = st.text_area(
        t("input"),
        value=chain.get("effective_input", ""),
        height=180,
        help="This is the effective input for the current agent. You can paste or edit anything here.",
        key="agent_chain_input_edit",
    )
    chain["effective_input"] = chain_input

    agent = agents[idx]
    st.markdown(f"### Current Agent {idx+1}/{len(agents)} — **{agent['name']}**")
    st.caption(agent.get("description", ""))

    # Pre-run controls
    model = st.selectbox(t("model"), MODEL_CHOICES, index=MODEL_CHOICES.index(agent.get("default_model", MODEL_CHOICES[0])) if agent.get("default_model") in MODEL_CHOICES else 0, key=f"agent_model_{agent['id']}")
    max_tokens = st.number_input(t("max_tokens"), min_value=256, max_value=32000, value=DEFAULT_MAX_TOKENS, step=256, key=f"agent_maxtok_{agent['id']}")
    temp = st.slider(t("temperature"), 0.0, 1.0, DEFAULT_TEMPERATURE, 0.05, key=f"agent_temp_{agent['id']}")

    sys_prompt = st.text_area(t("system_prompt"), value=agent.get("system_prompt", ""), height=120, key=f"agent_sys_{agent['id']}")
    user_prompt_tmpl = st.text_area(t("user_prompt"), value=agent.get("user_prompt", ""), height=160, key=f"agent_user_{agent['id']}")

    # Render template
    user_prompt = user_prompt_tmpl.replace("{{input}}", chain_input)

    colRun, colNext = st.columns([1, 1])
    with colRun:
        if st.button(t("run"), type="primary", key=f"run_agent_{agent['id']}"):
            provider = provider_from_model(model)
            module = "AgentStudio"
            ok, msg = preflight(provider, model, module, require_requests=(provider in ("openai", "anthropic", "grok")))
            if not ok:
                st.warning(f"{t('preflight_failed')}: {msg}\n\n{t('fix_by_setting')}")
                log_event(module, "warn", "blocked", provider, model, msg, meta={"agent_id": agent["id"]})
                return
            try:
                rid = set_active_run(module, provider, model)
                messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}]
                out, meta = call_llm(provider, model, messages, temperature=float(temp), max_tokens=int(max_tokens), module=module,
                                     extra={"agent_id": agent["id"], "agent_name": agent["name"], "input_chars": len(chain_input)})
                # Store outputs (raw + effective)
                record = {
                    "agent_id": agent["id"],
                    "agent_name": agent["name"],
                    "model": model,
                    "provider": provider,
                    "system_prompt": sys_prompt,
                    "user_prompt": user_prompt,
                    "raw_output": out,
                    "effective_output": out,
                }
                chain["outputs"].append(record)
                st.session_state.artifacts[f"agent_{agent['id']}_raw"] = out
                st.session_state.artifacts[f"agent_{agent['id']}_effective"] = out
                finish_active_run("done", {"agent_id": agent["id"], "out_chars": len(out)})
                st.success("Agent run completed.")
            except Exception as e:
                log_event("AgentStudio", "error", "exception", provider, model, str(e), meta={"agent_id": agent["id"]})
                finish_active_run("error", {"error": str(e)})
                st.error(f"Agent failed: {e}")

    with colNext:
        if st.button(t("run_next"), key=f"next_agent_{agent['id']}"):
            chain["index"] = min(chain["index"] + 1, len(agents) - 1)
            # If we have an output, set next input to last effective output
            if chain["outputs"]:
                chain["effective_input"] = chain["outputs"][-1].get("effective_output", chain["effective_input"])
            st.rerun()

    st.markdown("### Outputs (Editable → Effective)")
    if not chain["outputs"]:
        st.caption("No outputs yet.")
    else:
        last = chain["outputs"][-1]
        st.caption("Edit the effective output below; it becomes the input for the next agent when you click Run Next.")
        view = st.radio("View", [t("markdown_view"), t("text_view")], horizontal=True, key="agent_out_view")
        eff = st.text_area("Effective output", value=last.get("effective_output", ""), height=260, key="agent_eff_edit")
        last["effective_output"] = eff
        st.session_state.artifacts[f"agent_{last['agent_id']}_effective"] = eff

        if view == t("markdown_view"):
            st.markdown("#### Preview")
            st.markdown(eff, unsafe_allow_html=True)

        with st.expander("Raw output (read-only)", expanded=False):
            st.code(last.get("raw_output", ""), language="markdown")


# -----------------------------
# Module: AI Note Keeper (9 Magics)
# -----------------------------

MAGICS = [
    # Existing 6 (generic names; align to your existing ones)
    ("Executive Summary Builder", "Turn the note into a crisp executive summary + key bullets."),
    ("Action Items Extractor", "Extract action items with owners (placeholders) and deadlines (placeholders)."),
    ("Risk & Mitigation Draft", "Identify risks and propose mitigations, marking uncertainty explicitly."),
    ("Meeting Minutes Formatter", "Format as meeting minutes: attendees, agenda, decisions, next steps."),
    ("Regulatory Checklist Generator", "Convert note into a regulatory checklist; avoid hallucinations."),
    ("Keyword Highlighter/Refiner", "Refine keyword list; highlight keywords in coral color."),

    # New 3
    ("Traceability Matrix Builder", "Map claims/requirements/questions to suggested evidence types, gaps, and status."),
    ("Contradiction & Ambiguity Detector", "Detect contradictions/ambiguity; propose rewrites and clarifying questions."),
    ("Regulatory-Ready Rewrite (Localized Tone)", "Rewrite in regulatory formal + internal actionable tone, respecting chosen language."),
]

def note_keeper_tab():
    st.markdown(f"## {t('note_keeper')}")
    wow_indicator()
    nk = st.session_state.note_keeper

    st.markdown("### Note Input")
    nk["note_input"] = st.text_area(t("note_input"), value=nk.get("note_input", ""), height=220, key="note_input_area")

    colA, colB, colC = st.columns([1, 1, 1])
    with colA:
        model = st.selectbox(t("model"), MODEL_CHOICES, index=MODEL_CHOICES.index("gpt-4o-mini") if "gpt-4o-mini" in MODEL_CHOICES else 0, key="note_model")
    with colB:
        max_tokens = st.number_input(t("max_tokens"), min_value=256, max_value=32000, value=DEFAULT_MAX_TOKENS, step=256, key="note_maxtok")
    with colC:
        temp = st.slider(t("temperature"), 0.0, 1.0, DEFAULT_TEMPERATURE, 0.05, key="note_temp")

    out_lang = st.selectbox("Output language (content)", ["English", "繁體中文"], index=0 if st.session_state.lang == "English" else 1, key="note_out_lang")

    default_organize_prompt = (
        "You are an AI Notekeeper. Transform the pasted note into an organized Markdown note.\n"
        "Requirements:\n"
        "- Use clear headings and bullet points.\n"
        "- Add sections: Summary, Key Points, Decisions (if any), Open Questions, Action Items.\n"
        f"- Identify key terms and highlight them using HTML spans with coral color: <span style=\"color:{CORAL}; font-weight:600;\">KEYWORD</span>\n"
        "- Do not hallucinate facts not present in the note; mark uncertainty.\n"
    )

    st.markdown("### Organize Note Prompt (Editable)")
    org_prompt = st.text_area(t("prompt"), value=nk.get("organize_prompt") or default_organize_prompt, height=180, key="org_prompt")
    nk["organize_prompt"] = org_prompt

    colOrg, colPin = st.columns([1, 1])
    with colOrg:
        if st.button(t("organize_note"), type="primary"):
            if not (nk.get("note_input") or "").strip():
                st.warning("Note input is empty.")
            else:
                provider = provider_from_model(model)
                module = "NoteKeeper/Organize"
                ok, msg = preflight(provider, model, module, require_requests=(provider in ("openai", "anthropic", "grok")))
                if not ok:
                    st.warning(f"{t('preflight_failed')}: {msg}\n\n{t('fix_by_setting')}")
                    log_event(module, "warn", "blocked", provider, model, msg, meta={})
                else:
                    try:
                        rid = set_active_run(module, provider, model)
                        sys_prompt = "You are a careful assistant. Follow instructions exactly; never expose secrets."
                        user_prompt = f"{org_prompt}\n\nLANGUAGE: {out_lang}\n\nNOTE:\n{nk['note_input']}"
                        out, meta = call_llm(provider, model, [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}],
                                            temperature=float(temp), max_tokens=int(max_tokens), module=module,
                                            extra={"input_chars": len(nk["note_input"]), "lang_out": out_lang})
                        nk["organized_md"] = out
                        nk["organized_effective"] = out
                        st.session_state.artifacts["note_organized_md"] = out
                        finish_active_run("done", {"out_chars": len(out)})
                        st.success("Note organized.")
                    except Exception as e:
                        log_event(module, "error", "exception", provider, model, str(e), meta={})
                        finish_active_run("error", {"error": str(e)})
                        st.error(f"Organize failed: {e}")

    with colPin:
        if st.button(t("pin_prompt")):
            nk["pinned_prompt"] = org_prompt
            st.success("Pinned.")

    if nk.get("pinned_prompt"):
        with st.expander(t("pinned_prompt"), expanded=False):
            st.code(nk["pinned_prompt"], language="text")

    st.markdown("### Organized Note (Editable → Effective)")
    view = st.radio("View", [t("markdown_view"), t("text_view")], horizontal=True, key="note_view")
    eff = st.text_area("Effective note", value=nk.get("organized_effective", ""), height=280, key="note_eff_edit")
    nk["organized_effective"] = eff
    st.session_state.artifacts["note_effective"] = eff

    if view == t("markdown_view") and eff:
        st.markdown("#### Preview")
        st.markdown(eff, unsafe_allow_html=True)

    st.markdown("### AI Magics (9)")
    magic_name = st.selectbox(t("ai_magic"), [m[0] for m in MAGICS], key="magic_select")
    magic_desc = dict(MAGICS).get(magic_name, "")
    st.caption(magic_desc)

    magic_prompt = st.text_area(
        "Magic prompt (editable)",
        value=(
            f"Apply the following transformation to the note.\n"
            f"Magic: {magic_name}\n"
            f"Description: {magic_desc}\n"
            f"Rules: Do not hallucinate. If uncertain, say so.\n"
            f"Language: {out_lang}\n"
        ),
        height=140,
        key="magic_prompt",
    )

    if st.button(t("apply_magic"), type="primary"):
        if not (eff or "").strip():
            st.warning("No effective note to transform.")
        else:
            provider = provider_from_model(model)
            module = "NoteKeeper/Magic"
            ok, msg = preflight(provider, model, module, require_requests=(provider in ("openai", "anthropic", "grok")))
            if not ok:
                st.warning(f"{t('preflight_failed')}: {msg}\n\n{t('fix_by_setting')}")
                log_event(module, "warn", "blocked", provider, model, msg, meta={"magic": magic_name})
            else:
                try:
                    rid = set_active_run(module, provider, model)
                    sys_prompt = "You are a precise assistant. Follow the magic instructions."
                    user_prompt = f"{magic_prompt}\n\nNOTE:\n{eff}"
                    out, meta = call_llm(provider, model, [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}],
                                        temperature=float(temp), max_tokens=int(max_tokens), module=module,
                                        extra={"magic": magic_name, "input_chars": len(eff)})
                    nk["magic_output"] = out
                    nk["magic_effective"] = out
                    st.session_state.artifacts[f"note_magic_{magic_name}"] = out
                    finish_active_run("done", {"magic": magic_name, "out_chars": len(out)})
                    st.success("Magic applied.")
                except Exception as e:
                    log_event(module, "error", "exception", provider, model, str(e), meta={"magic": magic_name})
                    finish_active_run("error", {"error": str(e), "magic": magic_name})
                    st.error(f"Magic failed: {e}")

    if nk.get("magic_effective"):
        st.markdown("### Magic Output (Editable → Effective)")
        mv = st.radio("View", [t("markdown_view"), t("text_view")], horizontal=True, key="magic_view")
        meff = st.text_area("Effective magic output", value=nk.get("magic_effective", ""), height=240, key="magic_eff_edit")
        nk["magic_effective"] = meff
        if mv == t("markdown_view"):
            st.markdown("#### Preview")
            st.markdown(meff, unsafe_allow_html=True)

        st.download_button(
            label=f"{t('download')} magic.md",
            data=meff.encode("utf-8"),
            file_name="note_magic.md",
            mime="text/markdown",
        )


# -----------------------------
# Module: Live Log
# -----------------------------

def live_log_tab():
    st.markdown(f"## {t('live_log')}")
    wow_indicator()

    events = st.session_state.events
    if not events:
        st.caption("No events yet.")
        return

    # Filters
    colF1, colF2, colF3 = st.columns([1, 1, 2])
    with colF1:
        sev = st.selectbox(t("filter") + " severity", ["all", "info", "warn", "error"], index=0)
    with colF2:
        module = st.selectbox(t("filter") + " module", ["all"] + sorted(list({e.get("module") for e in events})), index=0)
    with colF3:
        q = st.text_input(t("search"), value="")

    filt = []
    for e in events:
        if sev != "all" and e.get("severity") != sev:
            continue
        if module != "all" and e.get("module") != module:
            continue
        blob = json.dumps(e, ensure_ascii=False)
        if q and q.lower() not in blob.lower():
            continue
        filt.append(e)

    st.caption(f"Showing {len(filt)} / {len(events)} events")

    # Display as dataframe-like table
    st.dataframe(
        [{
            "ts_utc": e.get("ts_utc"),
            "run_id": e.get("run_id"),
            "module": e.get("module"),
            "severity": e.get("severity"),
            "event_type": e.get("event_type"),
            "model": e.get("model"),
            "message": e.get("message"),
        } for e in filt[::-1][:200]],
        use_container_width=True,
        hide_index=True,
    )

    # Export
    export_jsonl = "\n".join([json.dumps(e, ensure_ascii=False) for e in events])
    export_txt = "\n".join([f"{e.get('ts_utc')} {e.get('severity').upper()} {e.get('module')} {e.get('event_type')} {e.get('model')}: {e.get('message')}" for e in events])

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(t("export_log") + " (.jsonl)", data=export_jsonl.encode("utf-8"), file_name="smartmed_log.jsonl", mime="application/jsonl")
    with c2:
        st.download_button(t("export_log") + " (.txt)", data=export_txt.encode("utf-8"), file_name="smartmed_log.txt", mime="text/plain")


# -----------------------------
# About
# -----------------------------

def about_tab():
    st.markdown(f"## {t('about')}")
    wow_indicator()
    st.markdown(
        f"""
        <div class="wow-card">
          <div style="display:flex; flex-direction:column; gap:8px;">
            <div><b>{APP_NAME}</b> • v{APP_VERSION}</div>
            <div style="opacity:0.85;">{APP_SUBTITLE}</div>
            <div style="opacity:0.8;">
              Multi-provider routing (Gemini/OpenAI/Anthropic/Grok), agent-by-agent execution from agents.yaml,
              Guidance OCR + Step 3 generator with constraints, AI Note Keeper with 9 magics,
              WOW observability (Interactive Indicator, Live Log, Interactive Dashboard).
            </div>
            <div class="wow-kv" style="margin-top:8px;">
              <div class="k">Security</div><div class="v">Environment-first keys; UI fallback is session-only; never display env keys</div>
              <div class="k">Storage</div><div class="v">Session-state only by default (no server persistence)</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# Main
# -----------------------------

def main():
    st.set_page_config(page_title=APP_NAME, layout="wide")

    ensure_state()
    sidebar_settings()
    inject_wow_css(st.session_state.theme, st.session_state.painter_style)

    st.markdown(f"# {t('app_title')}")
    st.caption(t("app_sub"))

    tabs = st.tabs([t("dashboard"), t("guidance"), t("agent_studio"), t("note_keeper"), t("live_log"), t("about")])
    with tabs[0]:
        dashboard_tab()
    with tabs[1]:
        guidance_tab()
    with tabs[2]:
        agent_studio_tab()
    with tabs[3]:
        note_keeper_tab()
    with tabs[4]:
        live_log_tab()
    with tabs[5]:
        about_tab()

if __name__ == "__main__":
    main()
