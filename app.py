import json
import os
import shutil
import streamlit as st
import pandas as pd
import groq as groq_module
from datetime import datetime

from utils.llm_client import chat
from tools.tool_schemas import TOOL_SCHEMAS
from tools.csv_loader import load_csv
from tools.code_executor import execute_code
from tools.chart_generator import generate_chart
from utils.narrator import generate_narrative
from tools.forecaster import forecast
from utils.pdf_generator import generate_pdf

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Data Analyst Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #0F1117; }

    [data-testid="stSidebar"] {
        background: #1A1D27 !important;
        border-right: 1px solid #2A2D3E;
    }
    [data-testid="stSidebar"] * { color: #C8CADB !important; }
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #FFFFFF !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
    }
    [data-testid="stSidebar"] .stButton > button {
        background: #23263A !important;
        color: #A0A3B8 !important;
        border: 1px solid #2E3148 !important;
        border-radius: 8px !important;
        font-size: 12px !important;
        font-weight: 400 !important;
        text-align: left !important;
        padding: 8px 12px !important;
        margin-bottom: 4px !important;
        white-space: normal !important;
        height: auto !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #2E3148 !important;
        color: #FFFFFF !important;
        border-color: #4C6EF5 !important;
    }

    .main .block-container {
        padding: 2rem 2.5rem 3rem;
        max-width: 1100px;
    }
    .hero-title {
        font-size: 32px;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: -0.5px;
        line-height: 1.2;
        margin-bottom: 6px;
    }
    .hero-title span {
        background: linear-gradient(135deg, #4C6EF5 0%, #748FFC 50%, #9775FA 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .hero-sub {
        font-size: 14px;
        color: #6B6F8A;
        margin-bottom: 28px;
    }

    .stTextInput > div > div > input {
        background: #1A1D27 !important;
        border: 1.5px solid #2A2D3E !important;
        border-radius: 10px !important;
        color: #FFFFFF !important;
        font-size: 15px !important;
        padding: 14px 18px !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #4C6EF5 !important;
        box-shadow: 0 0 0 3px rgba(76,110,245,0.15) !important;
    }
    .stTextInput > div > div > input::placeholder { color: #454869 !important; }

    .main .stButton > button {
        background: linear-gradient(135deg, #4C6EF5, #9775FA) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        padding: 13px 24px !important;
        width: 100% !important;
        letter-spacing: 0.02em !important;
    }
    .main .stButton > button:hover { opacity: 0.88 !important; }

    .section-hdr {
        font-size: 11px;
        font-weight: 600;
        color: #4C6EF5;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin: 28px 0 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .section-hdr::after {
        content: '';
        flex: 1;
        height: 1px;
        background: #2A2D3E;
    }

    [data-testid="stMetric"] {
        background: #1A1D27;
        border: 1px solid #2A2D3E;
        border-radius: 10px;
        padding: 16px 20px;
    }
    [data-testid="stMetric"] label {
        color: #6B6F8A !important;
        font-size: 11px !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
    }
    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 28px !important;
        font-weight: 700 !important;
    }

    .narrative-box {
        background: #1A1D27;
        border: 1px solid #2A2D3E;
        border-left: 4px solid #4C6EF5;
        border-radius: 10px;
        padding: 22px 26px;
        font-size: 14px;
        line-height: 1.9;
        color: #C8CADB;
    }
    .chart-wrap {
        background: #1A1D27;
        border: 1px solid #2A2D3E;
        border-radius: 10px;
        padding: 6px;
        overflow: hidden;
    }

    [data-testid="stDataFrame"] { background: #23263A !important; border-radius: 8px !important; }
    [data-testid="stDataFrame"] * { color: #C8CADB !important; font-size: 12px !important; }

    .stCaption { color: #454869 !important; font-size: 11px !important; }
    .stRadio label { color: #A0A3B8 !important; font-size: 13px !important; }

    [data-testid="stDownloadButton"] > button {
        background: #23263A !important;
        color: #748FFC !important;
        border: 1px solid #2E3148 !important;
        border-radius: 8px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        padding: 8px 16px !important;
        margin-top: 8px !important;
    }

    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #0F1117; }
    ::-webkit-scrollbar-thumb { background: #2A2D3E; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #4C6EF5; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────
DEMO_CSV   = "data/sales_data.csv"
UPLOAD_CSV = "data/uploaded_data.csv"

TOOL_REGISTRY = {
    "load_csv":       load_csv,
    "execute_code":   execute_code,
    "generate_chart": generate_chart,
    "forecast":       forecast,
}

# ── Session state defaults ────────────────────────────────────
if "chat_history"     not in st.session_state:
    st.session_state["chat_history"]     = []
if "followup_counter" not in st.session_state:
    st.session_state["followup_counter"] = 0
if "csv_path"         not in st.session_state:
    st.session_state["csv_path"]         = DEMO_CSV

SYSTEM_PROMPT = """You are a Data Analyst Agent. Use ReAct: Thought then Action.
IMPORTANT: Never write plans or outlines. Always immediately call a tool after each Thought. If you know what to do, DO IT — call the tool now.

Tools:
1. load_csv(filepath) — call FIRST always
2. execute_code(code) — pandas code, always end with result=...
3. generate_chart(code, filename) — matplotlib, use ax/fig/COLORS/apply_style, no plt.show()
4. forecast(periods, date_col, value_col, freq) — Prophet forecasting for future predictions

Rules:
- The dataframe is already loaded as `df` — NEVER use pd.read_csv() or import statements
- Always compute revenue first: df['revenue'] = df['units_sold'] * df['unit_price']
- ALWAYS return the FULL table in execute_code, never just the winner. Example:
    df['revenue'] = df['units_sold'] * df['unit_price']
    result = df.groupby('category')['revenue'].sum().sort_values(ascending=False).reset_index()
  NOT: result = df.groupby('category')['revenue'].sum().idxmax()
- Always end execute_code with result = ...
- Use simple groupby: df.groupby('col')['col2'].sum() — never use .apply() with lambda
- ALWAYS call generate_chart after execute_code — never skip visualization
- CRITICAL: generate_chart code MUST recompute all data from df from scratch — never reference execute_code variables
- CRITICAL: Never call plt.savefig(), plt.show(), plt.figure(), plt.subplots() in generate_chart
- CRITICAL: Always call apply_style(ax, 'title') as the last line in generate_chart
- Use forecast tool when user asks about predictions, future trends, or next N months
- Final answer must include actual numbers from the analysis: ## Key Findings, ## Numbers, ## Insight

Example of correct execute_code:
df['revenue'] = df['units_sold'] * df['unit_price']
result = df.groupby('category')['revenue'].sum().sort_values(ascending=False).reset_index()

Example of correct generate_chart code:
df['revenue'] = df['units_sold'] * df['unit_price']
data = df.groupby('category')['revenue'].sum().sort_values(ascending=False)
ax.bar(data.index, data.values, color=COLORS[:len(data)])
apply_style(ax, 'Revenue by Category 2024')"""


# ── Helpers ───────────────────────────────────────────────────
def _trim(tool_result: str) -> str:
    try:
        data = json.loads(tool_result)
        if "preview" in data:
            data.pop("preview", None)
            data.pop("null_counts", None)
            return json.dumps(data)
        if "output" in data and len(str(data["output"])) > 600:
            data["output"] = str(data["output"])[:600] + "...[truncated]"
            return json.dumps(data)
        return tool_result
    except Exception:
        return tool_result[:800]


def _render_trace(placeholder, steps: list):
    type_cfg = {
        "thought":     ("#9775FA", "#1E1A2E", "🧠", "Thought"),
        "action":      ("#4C6EF5", "#141829", "🔧", "Action"),
        "observation": ("#20C997", "#0D2118", "👁️",  "Observation"),
        "answer":      ("#51CF66", "#0D1F12", "✅", "Final Answer"),
        "error":       ("#FF6B6B", "#2A1010", "❌", "Error"),
    }
    with placeholder.container():
        for step in steps:
            color, bg, icon, label = type_cfg.get(
                step["type"], ("#748FFC", "#1A1D27", "•", step["type"])
            )
            tool_str = ""
            if step.get("tool_name"):
                args_preview = {}
                for k, v in step.get("tool_args", {}).items():
                    if k == "code":
                        lines = v.strip().split("\n")
                        args_preview[k] = lines[0] + ("..." if len(lines) > 1 else "")
                    else:
                        args_preview[k] = v
                tool_str = (
                    f"<code style='font-size:11px;color:{color};"
                    f"font-family:JetBrains Mono,monospace;background:#0F1117;"
                    f"padding:2px 6px;border-radius:4px;'>"
                    f"{step['tool_name']}({json.dumps(args_preview)[1:-1]})</code>"
                )

            content = step["content"][:420]
            if len(step["content"]) > 420:
                content += "…"

            st.markdown(
                f"""<div style='background:{bg};border:1px solid {color}33;
                border-left:3px solid {color};border-radius:8px;
                padding:10px 14px;margin-bottom:6px;font-size:13px;
                font-family:Inter,sans-serif;'>
                <div style='display:flex;align-items:center;gap:6px;margin-bottom:5px;'>
                    <span>{icon}</span>
                    <strong style='color:{color};font-size:11px;letter-spacing:0.08em;
                    text-transform:uppercase;'>{label}</strong>
                    <span style='color:#454869;font-size:11px;margin-left:auto;'>
                    step {step['step']}</span>
                </div>
                <div style='color:#C8CADB;line-height:1.6;'>{content}</div>
                {f"<div style='margin-top:7px;'>{tool_str}</div>" if tool_str else ""}
                </div>""",
                unsafe_allow_html=True
            )


# ── Core agent loop ───────────────────────────────────────────
def run_agent(user_question: str, csv_path: str,
              trace_placeholder, status_placeholder) -> dict:

    prior = st.session_state.get("chat_history", [])

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *prior[-6:],
        {"role": "user", "content": (
            f"CSV file is at: {csv_path}\n\n"
            f"Question: {user_question}\n\n"
            f"Start with Thought, then call load_csv first."
        )}
    ]

    trace_steps = []
    charts      = []
    error_count = 0
    MAX_ERRORS     = 3
    MAX_ITERATIONS = 10

    def add_trace(step_type, content, tool_name=None, tool_args=None):
        trace_steps.append({
            "step":      len(trace_steps) + 1,
            "type":      step_type,
            "content":   content,
            "tool_name": tool_name,
            "tool_args": tool_args or {},
        })
        _render_trace(trace_placeholder, trace_steps)

    def extract_thought(content):
        if not content:
            return
        for line in content.split("\n"):
            line = line.strip()
            if line.lower().startswith("thought:"):
                t = line[len("thought:"):].strip()
                if t:
                    add_trace("thought", t)
                return
        if content.strip():
            add_trace("thought", content.strip()[:300])

    for iteration in range(1, MAX_ITERATIONS + 1):
        status_placeholder.markdown(
            f"<div style='color:#748FFC;font-size:13px;padding:6px 0;'>"
            f"⚙️ Agent thinking… step {iteration}</div>",
            unsafe_allow_html=True
        )

        try:
            forced   = "required" if iteration <= 2 else "auto"
            response = chat(messages, tools=TOOL_SCHEMAS, tool_choice=forced)
        except groq_module.BadRequestError as e:
            add_trace("error", f"Bad request: {str(e)[:200]}")
            messages.append({
                "role": "user",
                "content": "Your last tool call was malformed. Retry and include ALL required arguments, especially 'filename' for generate_chart."
            })
            try:
                response = chat(messages, tools=TOOL_SCHEMAS, tool_choice="auto")
            except Exception as e2:
                add_trace("error", f"Retry also failed: {str(e2)[:200]}")
                break
        except Exception as e:
            add_trace("error", f"API error: {str(e)[:200]}")
            break

        message = response.choices[0].message

        if message.tool_calls:
            extract_thought(message.content)

            messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name":      tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}

                add_trace("action", f"Calling {tool_name}",
                          tool_name=tool_name, tool_args=tool_args)

                status_placeholder.markdown(
                    f"<div style='color:#4C6EF5;font-size:13px;padding:6px 0;'>"
                    f"🔧 Running: <code style='background:#141829;padding:2px 6px;"
                    f"border-radius:4px;color:#748FFC;'>{tool_name}</code></div>",
                    unsafe_allow_html=True
                )

                tool_fn     = TOOL_REGISTRY.get(tool_name)
                tool_result = tool_fn(**tool_args) if tool_fn else json.dumps(
                    {"status": "error", "message": f"Unknown tool: {tool_name}"}
                )

                try:
                    rd = json.loads(tool_result)
                    if rd.get("status") == "error":
                        error_count += 1
                        add_trace("error", rd.get("message", "")[:300])
                    else:
                        error_count = 0
                        preview = tool_result[:350] + ("…" if len(tool_result) > 350 else "")
                        add_trace("observation", preview)
                    if "chart_path" in rd:
                        charts.append(rd["chart_path"])
                except Exception:
                    pass

                messages.append({
                    "role":         "tool",
                    "tool_call_id": tool_call.id,
                    "content":      _trim(tool_result)
                })

            if error_count >= MAX_ERRORS:
                add_trace("error", "Too many consecutive errors. Stopping.")
                break

        else:
            final_answer = message.content
            add_trace("answer", final_answer)

            status_placeholder.markdown(
                "<div style='color:#20C997;font-size:13px;padding:6px 0;'>"
                "🗣️ Generating insight narrative…</div>",
                unsafe_allow_html=True
            )

            from groq import Groq
            _client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            _prompt = (
                f"Question: {user_question}\n\nAnalysis:\n{final_answer}\n\n"
                f"Write a 4-section insight report with: ## Summary, "
                f"## Key Numbers, ## Insight, ## Recommendation. "
                f"Under 200 words. Be specific."
            )
            _r = _client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": _prompt}],
                temperature=0,
                max_tokens=1024,
            )
            narrative = _r.choices[0].message.content

            st.session_state["chat_history"].append({
                "role": "user", "content": user_question
            })
            st.session_state["chat_history"].append({
                "role": "assistant", "content": final_answer
            })

            status_placeholder.empty()

            return {
                "answer":     final_answer,
                "narrative":  narrative,
                "charts":     charts,
                "iterations": iteration,
                "trace":      trace_steps,
            }

    status_placeholder.empty()
    return {
        "answer":     "Agent could not complete within the iteration limit.",
        "narrative":  "",
        "charts":     charts,
        "iterations": MAX_ITERATIONS,
        "trace":      trace_steps,
    }


# ══════════════════════════════════════════════════════════════
# SIDEBAR — runs first, sets csv_path in session state
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 📁 Data Source")

    data_source = st.radio(
        "Choose data",
        ["✨ Use demo dataset", "📂 Upload your CSV"],
        label_visibility="collapsed"
    )

    if data_source == "📂 Upload your CSV":
        uploaded = st.file_uploader(
            "Upload CSV", type=["csv"], label_visibility="collapsed"
        )
        if uploaded:
            with open(UPLOAD_CSV, "wb") as f:
                shutil.copyfileobj(uploaded, f)
            st.session_state["csv_path"] = UPLOAD_CSV
            st.success("✅ File uploaded!")
        else:
            st.info("Waiting for file…")
            st.session_state["csv_path"] = None
    else:
        st.session_state["csv_path"] = DEMO_CSV

    csv_path = st.session_state["csv_path"]

    if csv_path and os.path.exists(csv_path):
        load_csv(csv_path)
        st.markdown("---")
        st.markdown("**📋 Schema**")
        try:
            df_prev = pd.read_csv(csv_path)
            st.dataframe(
                pd.DataFrame({
                    "Column": df_prev.columns,
                    "Type":   [str(df_prev[c].dtype) for c in df_prev.columns]
                }),
                hide_index=True,
                use_container_width=True
            )
            st.caption(f"{len(df_prev)} rows · {len(df_prev.columns)} columns")
        except Exception:
            st.warning("Could not preview schema.")

    st.markdown("---")
    st.markdown("**💡 Try these**")
    examples = [
        "Which product category had the highest total revenue in 2024?",
        "Who is the top performing sales rep by revenue?",
        "Show monthly revenue trend for 2023 vs 2024",
        "Predict revenue for the next 3 months",
        "Which region has the highest units sold?",
        "What are the top 5 products by revenue?",
        "Compare Electronics vs Furniture revenue by region",
    ]
    for q in examples:
        if st.button(q, key=f"eq_{q[:25]}", use_container_width=True):
            st.session_state["question_input"] = q
            st.rerun()

    st.markdown("---")
    st.caption("🤖 LLaMA 3.3 70B via Groq\nReAct · pandas · matplotlib · Streamlit")


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════
st.markdown(
    '<div class="hero-title">Autonomous <span>Data Analyst</span> Agent</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="hero-sub">Ask anything about your data — the agent reasons, '
    'writes code, charts results, and narrates insights automatically.</div>',
    unsafe_allow_html=True
)

# Always read csv_path from session state here
csv_path = st.session_state.get("csv_path", DEMO_CSV)

# ── Input ─────────────────────────────────────────────────────
question = st.text_input(
    "Question",
    placeholder="e.g. Which product had the highest revenue in Q1?",
    label_visibility="collapsed",
    key="question_input"
)

col1, col2 = st.columns([5, 1])
with col1:
    analyze_btn = st.button("▶  Analyze", use_container_width=True)
analyze = analyze_btn

with col2:
    if st.button("Clear", use_container_width=True):
        for k in ["result", "last_q", "question_input",
                  "chat_history", "pending_followup"]:
            st.session_state.pop(k, None)
        st.session_state["followup_counter"] = 0
        st.rerun()

# ── Handle pending follow-up ──────────────────────────────────
if "pending_followup" in st.session_state:
    followup_q  = st.session_state.pop("pending_followup")
    _csv        = st.session_state.get("csv_path", DEMO_CSV)
    st.markdown('<div class="section-hdr">Reasoning Trace</div>',
                unsafe_allow_html=True)
    trace_ph  = st.empty()
    status_ph = st.empty()
    result    = run_agent(followup_q, _csv, trace_ph, status_ph)
    st.session_state["result"] = result
    st.session_state["last_q"] = followup_q

# ── Handle main Analyze button ────────────────────────────────
elif analyze:
    if not question.strip():
        st.warning("Please enter a question first.")
    elif not csv_path or not os.path.exists(csv_path):
        st.warning("Please select or upload a CSV file first.")
    else:
        st.markdown('<div class="section-hdr">Reasoning Trace</div>',
                    unsafe_allow_html=True)
        trace_ph  = st.empty()
        status_ph = st.empty()
        result    = run_agent(question, csv_path, trace_ph, status_ph)
        st.session_state["result"] = result
        st.session_state["last_q"] = question

# ── Show results ──────────────────────────────────────────────
if "result" in st.session_state:
    result = st.session_state["result"]

    if not analyze and "pending_followup" not in st.session_state:
        st.markdown('<div class="section-hdr">Reasoning Trace</div>',
                    unsafe_allow_html=True)
        trace_ph  = st.empty()
        status_ph = st.empty()
        _render_trace(trace_ph, result["trace"])

    # Metrics
    st.markdown('<div class="section-hdr">Run Summary</div>',
                unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    m1.metric("Reasoning Steps",  len(result["trace"]))
    m2.metric("Agent Iterations", result["iterations"])
    m3.metric("Charts Generated", len(result["charts"]))

    # Chart
    chart_list = result.get("charts", [])
    if not chart_list:
        import glob
        pngs = glob.glob("data/*.png")
        if pngs:
            latest = max(pngs, key=os.path.getmtime)
            chart_list = [latest]

    if chart_list:
        st.markdown('<div class="section-hdr">Generated Chart</div>',
                    unsafe_allow_html=True)
        for cp in chart_list:
            cp = cp.replace("\\", "/")
            if os.path.exists(cp):
                st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
                st.image(cp, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                with open(cp, "rb") as f:
                    st.download_button(
                        f"⬇️ Download {os.path.basename(cp)}", f,
                        file_name=os.path.basename(cp),
                        mime="image/png",
                        key=f"dl_{cp}"
                    )

    # Narrative
    if result.get("narrative"):
        st.markdown('<div class="section-hdr">Insight Report</div>',
                    unsafe_allow_html=True)
        st.markdown(
            f'<div class="narrative-box">{result["narrative"]}</div>',
            unsafe_allow_html=True
        )

    # Follow-up
    st.markdown('<div class="section-hdr">💬 Ask a follow-up</div>',
                unsafe_allow_html=True)

    followup = st.text_input(
        "Follow-up",
        placeholder='e.g. "Now show only the South region"',
        label_visibility="collapsed",
        key=f"followup_input_{st.session_state['followup_counter']}"
    )
    if st.button("▶ Ask follow-up", use_container_width=True):
        if followup.strip():
            st.session_state["pending_followup"] = followup
            st.session_state["followup_counter"] += 1
            st.rerun()

    # Memory clear
    if st.button("🗑 Clear conversation memory", use_container_width=True):
        st.session_state["chat_history"] = []
        st.session_state.pop("result", None)
        st.session_state["followup_counter"] = 0
        st.rerun()

    # PDF Export
    st.markdown('<div class="section-hdr">📄 Export Report</div>',
                unsafe_allow_html=True)

    if st.button("📄 Generate PDF Report", use_container_width=True):
        with st.spinner("Building PDF..."):
            try:
                pdf_path = generate_pdf(
                    question    = st.session_state.get("last_q", "Analysis"),
                    narrative   = result.get("narrative", ""),
                    chart_paths = result.get("charts", []),
                    output_path = "data/insight_report.pdf"
                )
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label     = "⬇️ Download PDF Report",
                        data      = f,
                        file_name = f"insight_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime      = "application/pdf",
                        key       = "pdf_download"
                    )
                st.success("✅ PDF ready!")
            except Exception as e:
                st.error(f"PDF generation failed: {str(e)}")

    # Raw answer
    with st.expander("🔎 View raw agent answer"):
        st.markdown(result["answer"])