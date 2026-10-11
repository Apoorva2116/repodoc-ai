import json
from pathlib import Path

import pandas as pd
import streamlit as st

from rag.qa import AVAILABLE_MODELS, LLM_MODEL
from rag.run_traced import run_traced

BASE_DIR = Path(__file__).resolve().parent
METRICS_FILE = BASE_DIR / "benchmark" / "corrected_metrics_phi3_rag.json"
EVENTS_FILE = BASE_DIR / "logs" / "rag_events.jsonl"

st.set_page_config(
    page_title="RepoDoc AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        color-scheme: light;
        --page-bg: #f5f7fc;
        --surface: #ffffff;
        --ink: #172033;
        --secondary: #53627d;
        --border: #dce3ef;
        --primary: #5145e5;
        --primary-hover: #4035c7;
    }

    html, body, [class*="css"] {
        font-family: Arial, Helvetica, sans-serif !important;
        color: var(--ink) !important;
    }

    .stApp, [data-testid="stMain"], [data-testid="stHeader"] {
        background: var(--page-bg) !important;
    }

    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div:first-child {
        background: #ffffff !important;
        border-right: 1px solid var(--border) !important;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] b,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] label p,
    [data-testid="stSidebar"] span {
        color: #202944 !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        border-radius: 9px;
        padding: 5px 8px;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label p {
        color: #202944 !important;
        font-weight: 600 !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
        background: #eeedff !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p {
        color: #4035c7 !important;
    }

    .brand {
        color: var(--ink) !important;
        font-size: 1.65rem;
        font-weight: 800;
        letter-spacing: -0.7px;
        margin-bottom: 0.15rem;
    }

    .brand span { color: var(--primary) !important; }

    .muted, .metric-label, .metric-note {
        color: var(--secondary) !important;
    }

    .eyebrow {
        color: #515e83 !important;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 0.4rem;
    }

    .hero-title {
        color: var(--ink) !important;
        font-size: 2.15rem;
        line-height: 1.25;
        font-weight: 800;
        letter-spacing: -1px;
        margin-bottom: 0.35rem;
    }

    h1, h2, h3, h4, h5, h6 {
        color: var(--ink) !important;
        font-weight: 700 !important;
    }

    .stMarkdown, .stMarkdown p, .stMarkdown li,
    .stMarkdown strong, .stMarkdown b {
        color: var(--ink);
    }

    .sidebar-card {
        background: #f8faff !important;
        border: 1px solid var(--border) !important;
        border-radius: 14px;
        padding: 1rem;
        margin-top: 1rem;
        color: #26344f !important;
    }

    .sidebar-card b, .sidebar-card p, .sidebar-card div {
        color: #26344f !important;
    }

    .panel {
        background: var(--surface) !important;
        color: var(--ink) !important;
        border: 1px solid var(--border) !important;
        border-radius: 15px;
        padding: 1.2rem;
        margin: 0.5rem 0 1rem;
        box-shadow: 0 3px 12px rgba(31, 44, 78, 0.04);
    }

    .panel-title {
        color: var(--ink) !important;
        font-size: 1.08rem;
        font-weight: 700;
        margin-bottom: 0.7rem;
    }

    .answer-label {
        color: var(--ink) !important;
        font-size: 1.3rem;
        font-weight: 800;
    }

    .status-pill {
        display: inline-block;
        background: #e5f8ef !important;
        color: #087f5b !important;
        padding: 6px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 700;
    }

    .stTextArea textarea, .stTextInput input {
        background: #ffffff !important;
        color: #172033 !important;
        -webkit-text-fill-color: #172033 !important;
        border: 1px solid #c6d1e2 !important;
        border-radius: 10px !important;
        font-size: 1rem !important;
        caret-color: #5145e5 !important;
    }

    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #635bfa !important;
        box-shadow: 0 0 0 2px rgba(99, 91, 250, 0.13) !important;
    }

    .stTextArea textarea::placeholder, .stTextInput input::placeholder {
        color: #65738c !important;
        -webkit-text-fill-color: #65738c !important;
        opacity: 1 !important;
    }

    [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p,
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p,
    .stCaption {
        color: #53627d !important;
    }

    div.stButton > button, div.stFormSubmitButton > button,
    [data-testid="stFormSubmitButton"] button {
        background: var(--primary) !important;
        color: #ffffff !important;
        border: 1px solid var(--primary) !important;
        border-radius: 9px !important;
        font-weight: 600 !important;
        min-height: 42px;
    }

    div.stButton > button p, div.stFormSubmitButton > button p,
    [data-testid="stFormSubmitButton"] button p {
        color: #ffffff !important;
    }

    div.stButton > button:hover, div.stFormSubmitButton > button:hover,
    [data-testid="stFormSubmitButton"] button:hover {
        background: var(--primary-hover) !important;
        border-color: var(--primary-hover) !important;
    }

    [data-baseweb="select"] > div {
        background: #ffffff !important;
        color: #172033 !important;
        border-color: #c6d1e2 !important;
    }

    [data-baseweb="select"] * { color: #172033 !important; }

    .metric-card {
        background: #ffffff !important;
        border: 1px solid var(--border) !important;
        border-radius: 13px;
        padding: 1rem;
        min-height: 95px;
    }

    .metric-label { font-size: 0.83rem; margin-bottom: 0.4rem; }

    .metric-value {
        color: #172033 !important;
        font-size: 1.55rem;
        font-weight: 800;
    }

    .metric-note { font-size: 0.77rem; margin-top: 0.2rem; }

    [data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }

    [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p,
    [data-testid="stMetricValue"], [data-testid="stMetricDelta"] {
        color: #172033 !important;
    }

    [data-testid="stDataFrame"] { background: #ffffff !important; }

    [data-testid="stExpander"] {
        background: #ffffff !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
    }

    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary p {
        color: #172033 !important;
    }

    .stMarkdown code {
        color: #3730a3 !important;
        background: #f0f1ff !important;
        border-radius: 4px;
        padding: 2px 4px;
    }

    [data-testid="stAlert"] p { color: #172033 !important; }
    hr { border-color: var(--border) !important; }
    a { color: #4338ca !important; }
    #MainMenu, footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


def read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return {}


def read_events():
    events = []
    if not EVENTS_FILE.exists():
        return events
    try:
        with open(EVENTS_FILE, "r", encoding="utf-8") as file:
            for line in file:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return events


def metric_card(label, value, note=""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def unique_sources(chunks):
    return list(dict.fromkeys(
        item.get("source", "unknown")
        for item in chunks
        if isinstance(item, dict)
    ))


# SIDEBAR
with st.sidebar:
    st.markdown(
        '<div class="brand">📚 RepoDoc <span>AI</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="muted">Your codebase, understood.</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    page = st.radio(
        "NAVIGATION",
        ["💬  Ask Repository", "📊  Benchmark", "📈  Observability"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("**⚙️ Language model**")

    selected_model = st.selectbox(
        "Choose model",
        AVAILABLE_MODELS,
        index=(
            AVAILABLE_MODELS.index(LLM_MODEL)
            if LLM_MODEL in AVAILABLE_MODELS
            else 0
        ),
        label_visibility="collapsed",
    )

    st.markdown(
        """
        <div class="sidebar-card">
            <b>🟢 Local AI environment</b>
            <p style="color:#53627d">Ollama · Local inference</p>
            <hr>
            <p style="color:#53627d">Repository</p>
            <b>realworld-flask</b>
            <br><br>
            <p style="color:#53627d">Embedding model</p>
            <b>nomic-embed-text</b>
            <br><br>
            <p style="color:#53627d">Vector database</p>
            <b>ChromaDB</b>
            <br><br>
            <p style="color:#53627d">Architecture</p>
            <b>Retrieval-Augmented Generation</b>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="color:#687791;text-align:center;margin-top:2rem">'
        'RepoDoc AI · Academic prototype</p>',
        unsafe_allow_html=True,
    )


# ASK REPOSITORY
if page == "💬  Ask Repository":
    st.markdown('<div class="eyebrow">Repository assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">Understand your codebase.</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="muted">Ask questions. Get answers grounded in your source code.</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    with st.form("repository_question_form"):
        question = st.text_area(
            "Your question",
            value=st.session_state.get("suggested_question", ""),
            placeholder="e.g. How is JWT authentication implemented?",
            height=100,
            max_chars=1000,
        )
        left, right = st.columns([5, 1])
        with left:
            st.caption(
                "ℹ️ Answers are based on retrieved repository evidence. "
                "The model may abstain when evidence is insufficient."
            )
        with right:
            submitted = st.form_submit_button("➤ Ask RepoDoc", use_container_width=True)

    if submitted:
        if not question.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner(
                f"Searching the repository and generating an answer with {selected_model}..."
            ):
                try:
                    result = run_traced(
                        question.strip(),
                        show_output=False,
                        model=selected_model,
                    )
                    st.session_state["last_result"] = result
                    st.session_state["last_question"] = question.strip()
                    st.session_state["suggested_question"] = ""
                except Exception as exc:
                    st.error(f"Could not process your question: {exc}")

    result = st.session_state.get("last_result")

    if result:
        answer = result.get("answer", "INSUFFICIENT EVIDENCE")
        chunks = result.get("chunks", [])
        sources = unique_sources(chunks)

        st.write("")
        answer_col, info_col = st.columns([2.3, 1], gap="medium")

        with answer_col:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            heading_col, badge_col = st.columns([2, 1])
            with heading_col:
                st.markdown('<div class="answer-label">✨ Answer</div>', unsafe_allow_html=True)
            with badge_col:
                if answer != "INSUFFICIENT EVIDENCE":
                    st.markdown(
                        '<div class="status-pill">● Response generated</div>',
                        unsafe_allow_html=True,
                    )

            st.markdown(answer)
            if sources:
                st.markdown("**Key source files**")
                for source in sources:
                    st.markdown(f"- `{source}`")
            st.markdown("</div>", unsafe_allow_html=True)

            m1, m2, m3 = st.columns(3)
            with m1:
                metric_card("Retrieval", f'{result.get("retrieval_seconds", 0):.2f}s', "Finding relevant chunks")
            with m2:
                metric_card("Generation", f'{result.get("generation_seconds", 0):.2f}s', "Language model response")
            with m3:
                metric_card("Source files", str(len(sources)), "Unique files retrieved")

            st.write("")
            with st.expander("📄 View retrieved evidence", expanded=False):
                if not chunks:
                    st.info("No repository evidence was retrieved.")
                else:
                    for index, chunk in enumerate(chunks, start=1):
                        st.markdown(f"**{index}. `{chunk.get('source', 'unknown')}`**")
                        distance = chunk.get("distance")
                        chunk_index = chunk.get("chunk_index", "?")
                        if isinstance(distance, (int, float)):
                            st.caption(f"Chunk {chunk_index} · Distance: {distance:.4f}")
                        else:
                            st.caption(f"Chunk {chunk_index}")
                        language = "python" if chunk.get("language") == "python" else "text"
                        st.code(chunk.get("text", ""), language=language)
                        st.divider()

            with st.expander("🔍 Request details"):
                st.write(f"**Model:** {result.get('model', selected_model)}")
                st.write(f"**Trace ID:** `{result.get('trace_id', 'N/A')}`")
                st.write(f"**Question:** {st.session_state.get('last_question', '')}")

        with info_col:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">🗂️ Repository information</div>', unsafe_allow_html=True)
            st.markdown("**Repository**")
            st.write("realworld-flask")
            st.markdown("**Files indexed**")
            st.write("40")
            st.markdown("**Chunks retrieved**")
            st.write(len(chunks))
            st.markdown("**Vector store**")
            st.write("ChromaDB")
            st.markdown("**Embedding model**")
            st.write("nomic-embed-text")
            st.markdown("**Selected LLM**")
            st.write(result.get("model", selected_model))
            st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.write("")
        st.markdown(
            """
            <div class="panel">
                <div class="panel-title">✨ Start exploring your codebase</div>
                <p style="color:#53627d">
                    Ask about functions, authentication, API routes, tests,
                    configuration, or how different components work together.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("**Try asking**")
        suggestions = [
            "How is JWT authentication implemented?",
            "How are API errors handled?",
            "How are user profiles tested?",
        ]
        cols = st.columns(3)
        for index, suggestion in enumerate(suggestions):
            with cols[index]:
                if st.button(suggestion, key=f"suggestion_{index}", use_container_width=True):
                    st.session_state["suggested_question"] = suggestion
                    st.rerun()


# BENCHMARK
elif page == "📊  Benchmark":
    st.markdown('<div class="eyebrow">Evaluation and quality</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">Benchmark results</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="muted">Evaluate how RepoDoc AI answers repository questions.</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    metrics = read_json(METRICS_FILE)
    if not metrics:
        st.warning("Benchmark metrics are unavailable. Run your evaluation script first.")
    else:
        st.info(
            "These saved results are for phi3:mini + RAG. "
            "Changing the sidebar model does not change these historical results."
        )
        cols = st.columns(3)
        with cols[0]:
            metric_card("Questions evaluated", metrics.get("total_questions", "N/A"), "Benchmark size")
        with cols[1]:
            hit_at_5 = metrics.get("hit_at_5")
            metric_card("Hit@5", f"{hit_at_5:.1%}" if isinstance(hit_at_5, (float, int)) else "N/A", "Retrieval coverage")
        with cols[2]:
            latency = metrics.get("average_latency_seconds")
            metric_card("Average latency", f"{latency:.1f}s" if isinstance(latency, (float, int)) else "N/A", "Per question")

        st.write("")
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">📈 Quality metrics</div>', unsafe_allow_html=True)

        metric_names = {
            "average_keyword_score": "Keyword score",
            "average_source_score": "Source score",
            "hit_at_5": "Hit@5",
            "unknown_detection_rate": "Unknown detection rate",
            "false_refusal_rate": "False refusal rate",
        }
        rows = []
        for key, label in metric_names.items():
            value = metrics.get(key)
            if isinstance(value, (int, float)):
                formatted = f"{value:.1%}" if 0 <= value <= 1 else f"{value:.3f}"
                rows.append({"Metric": label, "Score": formatted})

        if rows:
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

        st.caption(
            "Keyword and source scores are proxy metrics, not a complete semantic "
            "assessment. Unknown-detection and false-refusal rates depend on the "
            "benchmark's classification rules."
        )
        st.markdown("</div>", unsafe_allow_html=True)


# OBSERVABILITY
elif page == "📈  Observability":
    st.markdown('<div class="eyebrow">System monitoring</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">Observability</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="muted">Inspect requests, latency, failures, and retrieved sources.</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    events = read_events()
    requests = [event for event in events if event.get("event") == "rag_request"]

    if not requests:
        st.info(
            "No completed requests found yet. Ask a repository question "
            "to generate observability data."
        )
    else:
        successful = [item for item in requests if item.get("status") == "success"]
        failed = [item for item in requests if item.get("status") != "success"]
        latencies = [
            (item.get("retrieval_seconds", 0) or 0)
            + (item.get("generation_seconds", 0) or 0)
            for item in requests
        ]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card("Total requests", len(requests), "Logged requests")
        with c2:
            metric_card("Successful", len(successful), "Completed requests")
        with c3:
            metric_card("Failed", len(failed), "Requests with errors")
        with c4:
            metric_card("Average latency", f"{avg_latency:.1f}s", "Per request")

        st.write("")
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">⏱️ Request latency</div>', unsafe_allow_html=True)
        latency_df = pd.DataFrame({
            "Request": [f"Request {i}" for i in range(1, len(latencies) + 1)],
            "Latency (seconds)": latencies,
        })
        st.line_chart(latency_df.set_index("Request"))
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">🧾 Recent requests</div>', unsafe_allow_html=True)
        rows = []
        for item in reversed(requests[-20:]):
            rows.append({
                "Timestamp": item.get("timestamp", "N/A"),
                "Model": item.get("model", "N/A"),
                "Status": item.get("status", "unknown"),
                "Retrieval (s)": item.get("retrieval_seconds", 0),
                "Generation (s)": item.get("generation_seconds", 0),
                "Trace ID": item.get("trace_id", "N/A"),
                "Question": item.get("question", ""),
            })
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        source_counts = {}
        for item in requests:
            for source in item.get("sources", []):
                source_counts[source] = source_counts.get(source, 0) + 1

        if source_counts:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">📂 Most retrieved source files</div>', unsafe_allow_html=True)
            source_df = pd.DataFrame([
                {"Source": source, "Retrievals": count}
                for source, count in sorted(
                    source_counts.items(),
                    key=lambda pair: pair[1],
                    reverse=True,
                )
            ])
            st.bar_chart(source_df.set_index("Source"))
            st.markdown("</div>", unsafe_allow_html=True)
