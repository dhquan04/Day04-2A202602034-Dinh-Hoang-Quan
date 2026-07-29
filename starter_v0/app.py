from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import (
    ARTIFACTS_DIR,
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


ROOT = Path(__file__).parent
TRANSCRIPTS_DIR = ROOT / "transcripts"
SYSTEM_PROMPT_PATH = ARTIFACTS_DIR / "system_prompt.md"
TOOLS_PATH = ARTIFACTS_DIR / "tools.yaml"
PRODUCT_TOOL_NAMES = {"papers", "paper_text", "paper_bibtex"}
TOOL_ACTIVITY = {
    "papers": "Đang tìm paper trên arXiv",
    "paper_text": "Đang tải và đọc nội dung paper",
    "paper_bibtex": "Đang tạo trích dẫn BibTeX",
    "format": "Đang định dạng bản tóm tắt",
    "clarify": "Đang cần thêm thông tin từ bạn",
}
TOOL_STEP_LABELS = {
    "papers": "Tìm paper trên arXiv",
    "paper_text": "Đọc nội dung paper",
    "paper_bibtex": "Tạo mã BibTeX",
    "lookup": "Đối chiếu nguồn web",
    "fetch": "Đọc nội dung từ liên kết",
    "format": "Định dạng kết quả",
    "clarify": "Hỏi thêm thông tin",
    "policy": "Tra cứu chính sách",
    "timeline": "Đọc bài đăng tài khoản",
    "social_search": "Tìm trên mạng xã hội",
    "send": "Gửi nội dung đã xác nhận",
}


def make_transcript(version: str, provider_name: str, model: str | None) -> tuple[Path, dict[str, Any]]:
    artifact_version = build_artifact_version(version, SYSTEM_PROMPT_PATH, TOOLS_PATH)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(version), safe_slug(provider_name), timestamp])
    path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    return path, {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": provider_name,
        "model": model,
        "system_prompt": str(SYSTEM_PROMPT_PATH),
        "tools": str(TOOLS_PATH),
        "history_window": 5,
        "max_tool_rounds": 4,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }


def reset_session() -> None:
    # "live" is only a transcript label. Evaluation versions v0–v3 are run from the CLI.
    path, transcript = make_transcript("live", "openrouter", None)
    st.session_state.history = []
    st.session_state.chat_messages = []
    st.session_state.transcript_path = path
    st.session_state.transcript = transcript
    st.session_state.active_session = transcript["transcript_id"]
    st.session_state.chat_sessions.append({
        "id": transcript["transcript_id"],
        "title": "Cuộc trò chuyện mới",
        "history": st.session_state.history,
        "chat_messages": st.session_state.chat_messages,
        "transcript_path": path,
        "transcript": transcript,
    })


def ensure_session() -> None:
    if "transcript" not in st.session_state:
        st.session_state.chat_sessions = []
        reset_session()


def save_active_session() -> None:
    for session in st.session_state.chat_sessions:
        if session["id"] == st.session_state.active_session:
            session.update({
                "history": st.session_state.history,
                "chat_messages": st.session_state.chat_messages,
                "transcript_path": st.session_state.transcript_path,
                "transcript": st.session_state.transcript,
            })
            return


def load_session(session: dict[str, Any]) -> None:
    st.session_state.active_session = session["id"]
    st.session_state.history = session["history"]
    st.session_state.chat_messages = session["chat_messages"]
    st.session_state.transcript_path = session["transcript_path"]
    st.session_state.transcript = session["transcript"]


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def load_product_tool_declarations() -> list[dict[str, Any]]:
    """Expose only Paper Scout tools in the UI; base eval retains the full registry."""
    return [
        declaration
        for declaration in load_tool_declarations(TOOLS_PATH)
        if declaration["name"] in PRODUCT_TOOL_NAMES
    ]


def render_tool_trace(rounds: list[dict[str, Any]]) -> None:
    tool_rounds = [round_record for round_record in rounds if round_record.get("tool_calls")]
    if not tool_rounds:
        return

    total_calls = sum(len(round_record.get("tool_calls", [])) for round_record in tool_rounds)
    with st.expander(f"Xem tool trace · {total_calls} tool call(s)", expanded=False):
        for round_record in tool_rounds:
            round_no = round_record.get("round", "?")
            calls = round_record.get("tool_calls", [])
            results = round_record.get("tool_results", [])
            st.caption(f"Round {round_no}")
            if round_record.get("assistant_text"):
                st.caption(round_record["assistant_text"])
            for index, call in enumerate(calls):
                tool_name = call.get("name", "unknown")
                st.markdown(f"**{tool_name}**")
                st.code(compact_json(call.get("args", {})), language="json")
                if index < len(results):
                    result = results[index].get("result", {})
                    if isinstance(result, dict) and result.get("error"):
                        st.error(f"{result.get('error')}: {result.get('message', 'Unknown error')}")
                    st.code(compact_json(result), language="json")


def render_processing_steps(rounds: list[dict[str, Any]]) -> None:
    calls = [
        call
        for round_record in rounds
        for call in round_record.get("tool_calls", [])
    ]
    if not calls:
        return

    steps = []
    for index, call in enumerate(calls, start=1):
        tool_name = call.get("name", "tool")
        label = TOOL_STEP_LABELS.get(tool_name, tool_name)
        steps.append(
            f'<span class="process-step"><b>{index}</b>{label}<small>{tool_name}</small></span>'
        )
    st.markdown(
        '<div class="process-card"><span class="process-title">QUY TRÌNH XỬ LÝ</span>'
        + '<span class="process-flow">→</span>'.join(steps)
        + '</div>',
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="Research Paper Scout", page_icon="◈", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
    .stApp { background: #f7f7f8; color: #1f1f1f; }
    .block-container { max-width: 1380px; padding-top: 3.2rem; padding-bottom: 9rem; }
    [data-testid="stSidebar"] { background: #171717; border: 0; min-width: 300px; }
    [data-testid="stSidebar"] > div:first-child { min-width: 300px; }
    [data-testid="stSidebar"] * { color: #ececec !important; }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] li { font-size: 1.18rem !important; line-height: 1.65 !important; }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { font-size: 1.32rem !important; }
    [data-testid="stSidebar"] .stButton button { background: #2d2d2d; border: 1px solid #444; border-radius: 9px; font-weight: 550; font-size: 1.15rem !important; }
    [data-testid="stSidebar"] .stButton button p { font-size: 1.15rem !important; }
    [data-testid="stSidebar"] .stButton button:hover { background: #3b3b3b; border-color: #5d5d5d; }
    [data-testid="stSidebar"] hr { border-color: #3b3b3b; }
    .brand { display: flex; align-items: center; gap: .82rem; margin: .55rem 0 2.6rem; font-size: 1.4rem; font-weight: 650; }
    .brand-mark { width: 44px; height: 44px; display: grid; place-items: center; background: #10a37f; color: white; border-radius: 13px; font-size: 1.55rem; }
    .landing { text-align: center; padding-top: 15vh; }
    .landing h1 { font-size: clamp(3rem, 4.2vw, 4.45rem); letter-spacing: -.065em; margin: 0; color: #202123; }
    .landing p { color: #5f646c; font-size: 1.65rem; line-height: 1.6; margin: 1.2rem auto 3rem; max-width: 800px; }
    .suggestion-title { font-size: 1.48rem; color: #535861; font-weight: 700; margin: 0 0 1.15rem; text-transform: uppercase; letter-spacing: .07em; }
    div[data-testid="stChatInput"] { width: min(1280px, calc(100vw - 360px)) !important; max-width: none !important; margin: 0 auto !important; position: relative; }
    div[data-testid="stChatInput"] > div { width: 100% !important; max-width: none !important; align-items: center !important; padding: .6rem .7rem !important; }
    div[data-testid="stChatInput"] [data-baseweb="textarea"] { width: 100% !important; max-width: none !important; }
    div[data-testid="stChatInput"] textarea { background: white !important; border: 1px solid #d9d9e0 !important; border-radius: 21px !important; box-shadow: 0 3px 14px rgba(0,0,0,.07); font-size: 1.72rem !important; min-height: 82px !important; padding: 1.05rem 5.6rem 1.05rem 1.25rem !important; }
    div[data-testid="stChatInput"] button { position: absolute !important; right: 1.1rem !important; top: 50% !important; transform: translateY(-50%) !important; margin: 0 !important; width: 48px !important; height: 48px !important; min-height: 48px !important; padding: 0 !important; border-radius: 50% !important; display: grid !important; place-items: center !important; background: #10a37f !important; color: white !important; border: 0 !important; box-shadow: 0 3px 8px rgba(16,163,127,.28) !important; }
    div[data-testid="stChatInput"] button:hover { background: #087f62 !important; }
    div[data-testid="stChatInput"] button:disabled { background: #d9dee3 !important; color: #8a9199 !important; box-shadow: none !important; }
    div[data-testid="stChatInput"] textarea:focus { border-color: #10a37f !important; box-shadow: 0 0 0 2px rgba(16,163,127,.16); }
    [data-testid="stChatMessage"] { background: transparent; padding: 1.5rem .3rem; font-size: 1.35rem; }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] { font-size: 1.35rem !important; line-height: 1.8; }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li { font-size: 1.35rem !important; line-height: 1.8; }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h1 { font-size: 2.35rem !important; }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h2 { font-size: 2rem !important; }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h3 { font-size: 1.7rem !important; margin-top: 1.15rem; }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] ul,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] ol { padding-left: 1.7rem; }
    div[data-testid="stChatMessage"] p,
    div[data-testid="stChatMessage"] li,
    div[data-testid="stChatMessage"] a,
    div[data-testid="stChatMessage"] span { font-size: 1.62rem !important; line-height: 1.85 !important; }
    div[data-testid="stChatMessage"] h1 { font-size: 2.6rem !important; }
    div[data-testid="stChatMessage"] h2 { font-size: 2.25rem !important; }
    div[data-testid="stChatMessage"] h3 { font-size: 1.95rem !important; }
    div[data-testid="stChatMessage"] pre,
    div[data-testid="stChatMessage"] pre code,
    div[data-testid="stChatMessage"] pre span { font-size: 1.22rem !important; line-height: 1.65 !important; }
    div[data-testid="stChatMessage"] [data-testid="stExpander"] summary,
    div[data-testid="stChatMessage"] [data-testid="stExpander"] summary span { font-size: 1.25rem !important; }
    .stButton button { border-radius: 14px; border: 1px solid #dedee5; background: #fff; color: #303035; text-align: left; padding: 1rem 1.15rem; font-size: 1.12rem; min-height: 72px; }
    .stButton button:hover { border-color: #10a37f; color: #087a60; background: #f0fbf8; }
    [data-testid="stMain"] .stButton button,
    [data-testid="stMain"] .stButton button p { font-size: 1.55rem !important; font-weight: 600; }
    [data-testid="stMain"] .stButton button { min-height: 98px; padding: 1.2rem 1.4rem; }
    .sidebar-note { color: #c8c8c8 !important; font-size: 1.2rem; line-height: 1.9; }
    .trace-note { color: #737780; font-size: .82rem; margin-top: .2rem; }
    .process-card { display: flex; align-items: center; flex-wrap: wrap; gap: .65rem; margin: .7rem 0 1.25rem;
                    padding: .85rem 1rem; border: 1px solid #ccefe6; border-radius: 14px; background: #f1fbf8; }
    div[data-testid="stChatMessage"] .process-title { color: #087a60; font-size: .78rem !important; font-weight: 750; letter-spacing: .08em; margin-right: .25rem; }
    div[data-testid="stChatMessage"] .process-step { display: inline-flex; align-items: center; gap: .42rem; color: #1e443b; font-size: 1rem !important; font-weight: 600; }
    .process-step b { display: inline-grid; place-items: center; width: 1.45rem; height: 1.45rem; border-radius: 50%; background: #10a37f; color: white; font-size: .78rem; }
    div[data-testid="stChatMessage"] .process-step small { color: #4d756b; font-size: .78rem !important; font-weight: 500; }
    .process-flow { color: #5c867b; font-size: 1.2rem; }
    [data-testid="stBottom"] { background: linear-gradient(transparent, #f7f7f8 28%); padding: 1.2rem 0 1rem; }
    [data-testid="stBottom"] > div { width: 100%; margin: 0 auto; padding: 0; }
    @media (max-width: 900px) {
        div[data-testid="stChatInput"] { width: calc(100vw - 2rem) !important; }
    }
    .session-label { color: #9a9a9a !important; font-size: .73rem; font-weight: 700; letter-spacing: .08em; margin: 1.2rem 0 .45rem; }
    [data-testid="stSidebar"] .session-item button { background: transparent; border: 0; min-height: 38px; padding: .45rem .55rem; font-size: .91rem; }
    [data-testid="stSidebar"] .session-item button:hover { background: #2a2a2a; }
</style>
""", unsafe_allow_html=True)

provider_name = "openrouter"
model_override = ""
# This is a backend safety ceiling, not a required number of tool calls.
max_tool_rounds = 4
ensure_session()

with st.sidebar:
    st.markdown('<div class="brand"><span class="brand-mark">◈</span><span>Paper Scout</span></div>', unsafe_allow_html=True)
    if st.button("＋ Cuộc trò chuyện mới", use_container_width=True):
        reset_session()
        st.rerun()
    st.markdown('<p class="session-label">CUỘC TRÒ CHUYỆN</p>', unsafe_allow_html=True)
    for session in reversed(st.session_state.chat_sessions):
        with st.container():
            st.markdown('<div class="session-item">', unsafe_allow_html=True)
            label = f"● {session['title']}" if session["id"] == st.session_state.active_session else session["title"]
            if st.button(label, key=f"session_{session['id']}", use_container_width=True):
                load_session(session)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    st.divider()
    st.markdown("**KHẢ NĂNG**")
    st.markdown("""
    <div class="sidebar-note">
    • Tìm paper theo chủ đề<br>
    • Đọc một paper theo arXiv ID/URL<br>
    • Tóm tắt phương pháp và kết quả<br>
    • So sánh các paper liên quan
    </div>
    """, unsafe_allow_html=True)

transcript = st.session_state.transcript

if not st.session_state.chat_messages:
    st.markdown("""
    <section class="landing">
      <h1>Hôm nay bạn muốn nghiên cứu gì?</h1>
      <p>Tìm paper trên arXiv, đọc nội dung và nhận bản tóm tắt rõ ràng với nguồn dẫn.</p>
    </section>
    <p class="suggestion-title">Bắt đầu với một gợi ý</p>
    """, unsafe_allow_html=True)
    suggestion_columns = st.columns(3)
    suggestions = [
        "Tìm 3 paper về thuật toán RRT",
        "Paper mới về đánh giá AI agent",
        "So sánh RRT và RRT*",
    ]
    for column, suggestion in zip(suggestion_columns, suggestions):
        with column:
            if st.button(suggestion, use_container_width=True):
                st.session_state.pending_prompt = suggestion
                st.rerun()

for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("rounds"):
            render_processing_steps(message["rounds"])
            render_tool_trace(message["rounds"])

prompt = st.session_state.pop("pending_prompt", None) or st.chat_input(
    "Nhắn tin cho Paper Scout...",
)
if prompt:
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    if len(st.session_state.chat_messages) == 1:
        for session in st.session_state.chat_sessions:
            if session["id"] == st.session_state.active_session:
                session["title"] = prompt[:42] + ("…" if len(prompt) > 42 else "")
                break
    with st.chat_message("user"):
        st.markdown(prompt)

    turn_record: dict[str, Any] = {
        "turn_index": len(transcript["turns"]) + 1,
        "started_at": now_iso(),
        "user": prompt,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    with st.chat_message("assistant"):
        activity = st.status("Đang phân tích yêu cầu…", expanded=True)

        def show_tool_activity(event: dict[str, Any]) -> None:
            tool_name = event.get("tool", "tool")
            action = TOOL_ACTIVITY.get(tool_name, f"Đang chạy {tool_name}")
            if event.get("status") == "calling":
                activity.write(f"◌ {action}")
            else:
                result = event.get("result", {})
                if isinstance(result, dict) and result.get("error"):
                    activity.write(f"! {tool_name} gặp lỗi")
                else:
                    activity.write(f"✓ Hoàn tất: {tool_name}")

        with st.spinner("Đang chuẩn bị phản hồi..."):
            try:
                system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
                declarations = load_product_tool_declarations()
                provider = make_provider(provider_name)
                selected_model = model_override or getattr(provider, "default_model", None)
                messages = [
                    {"role": "system", "content": system_prompt},
                    *trim_history(st.session_state.history, 5),
                    {"role": "user", "content": prompt},
                ]
                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=to_openai_tools(declarations),
                    model=selected_model,
                    max_tool_rounds=max_tool_rounds,
                    on_tool_event=show_tool_activity,
                )
                turn_record.update(result)
                activity.update(label="Đã hoàn tất", state="complete", expanded=False)
                answer = result["assistant_text"] or "Không có phản hồi từ model."
                st.markdown(answer)
                render_processing_steps(result["rounds"])
                render_tool_trace(result["rounds"])
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": answer,
                    "rounds": result["rounds"],
                })
                st.session_state.history.extend([
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": answer},
                ])
            except Exception as exc:
                message = f"{type(exc).__name__}: {exc}"
                turn_record.update({"status": "provider_error", "error": message})
                activity.update(label="Không thể hoàn tất", state="error", expanded=True)
                st.error(f"Không thể hoàn tất yêu cầu: {message}")

    turn_record["ended_at"] = now_iso()
    transcript["turns"].append(turn_record)
    write_transcript(st.session_state.transcript_path, transcript)
    save_active_session()
    st.rerun()
#a