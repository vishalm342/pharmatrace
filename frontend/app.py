import os
import time
import requests
import streamlit as st
from storage import load_history, save_history

st.set_page_config(
    page_title="PharmaTrace",
    page_icon="🔬",
    layout="wide",
)

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
API_URL = os.getenv("API_URL", "https://pharmatrace-c6ut.onrender.com")

if "history" not in st.session_state:
    st.session_state.history = load_history()

if "latest_result" not in st.session_state:
    st.session_state.latest_result = None

if "api_status" not in st.session_state:
    st.session_state.api_status = "Unknown"

if "input_drug_a" not in st.session_state:
    st.session_state.input_drug_a = ""

if "input_drug_b" not in st.session_state:
    st.session_state.input_drug_b = ""


def check_api_health():
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        st.session_state.api_status = "Connected" if response.status_code == 200 else "Unavailable"
    except Exception:
        st.session_state.api_status = "Unavailable"


def status_style(review_status: str):
    mapping = {
        "NEEDS_CLINICAL_REVIEW": {
            "label": "Needs clinical review",
            "accent": "#F4A62A",
            "border": "rgba(244, 166, 42, 0.45)",
            "bg": "rgba(244, 166, 42, 0.08)",
        },
        "CAUTION_FLAGGED": {
            "label": "Caution flagged",
            "accent": "#E35D6A",
            "border": "rgba(227, 93, 106, 0.45)",
            "bg": "rgba(227, 93, 106, 0.08)",
        },
        "NO_LABEL_SIGNAL_FOUND": {
            "label": "No label signal found",
            "accent": "#4FB286",
            "border": "rgba(79, 178, 134, 0.45)",
            "bg": "rgba(79, 178, 134, 0.08)",
        },
        "ANALYSIS_UNAVAILABLE": {
            "label": "Analysis unavailable",
            "accent": "#94A3B8",
            "border": "rgba(148, 163, 184, 0.35)",
            "bg": "rgba(148, 163, 184, 0.08)",
        },
    }
    return mapping.get(
        review_status,
        {
            "label": review_status.replace("_", " ").title(),
            "accent": "#94A3B8",
            "border": "rgba(148, 163, 184, 0.35)",
            "bg": "rgba(148, 163, 184, 0.08)",
        },
    )


def inject_custom_css():
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 2.2rem;
            padding-bottom: 2rem;
            max-width: 1180px;
        }

        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(255,255,255,0.06);
        }

        .pt-header {
            margin-bottom: 1.25rem;
        }

        .pt-title {
            font-size: 3rem;
            font-weight: 800;
            line-height: 1.05;
            letter-spacing: -0.03em;
            margin: 0;
        }

        .pt-subtitle {
            color: #98A2B3;
            font-size: 1rem;
            margin-top: 0.35rem;
        }

        .pt-disclaimer {
            margin-top: 1rem;
            padding: 0.85rem 1rem;
            border-radius: 14px;
            background: rgba(244, 166, 42, 0.08);
            border: 1px solid rgba(244, 166, 42, 0.22);
            color: #E8ECF3;
            font-size: 0.95rem;
        }

        .pt-section-label {
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #98A2B3;
            margin-bottom: 0.55rem;
            font-weight: 700;
        }

        .pt-card {
            background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.015));
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 1.15rem 1.2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.12);
        }

        .pt-status-card {
            border-radius: 18px;
            padding: 1.2rem 1.2rem 1.1rem 1.2rem;
            margin-top: 0.75rem;
            margin-bottom: 0.85rem;
        }

        .pt-status-chip {
            display: inline-block;
            padding: 0.36rem 0.7rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.01em;
            margin-bottom: 0.8rem;
        }

        .pt-status-summary {
            font-size: 1rem;
            line-height: 1.75;
            color: #E8ECF3;
            margin: 0;
        }

        .pt-metric-card {
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 16px;
            padding: 0.95rem 1rem;
            height: 100%;
        }

        .pt-metric-label {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #98A2B3;
            margin-bottom: 0.45rem;
            font-weight: 700;
        }

        .pt-metric-value {
            font-size: 1.2rem;
            font-weight: 700;
            color: #F8FAFC;
            line-height: 1.3;
        }

        .pt-sidebar-note {
            font-size: 0.88rem;
            color: #AAB4C5;
            line-height: 1.6;
        }

        .stButton > button {
            border-radius: 12px;
        }

        div[data-testid="stForm"] {
            border: 0 !important;
            padding: 0 !important;
            background: transparent !important;
        }

        div[data-testid="stExpander"] {
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 14px;
            overflow: hidden;
        }

        div[data-testid="stTabs"] button {
            font-weight: 600;
        }

        .pt-spacer {
            height: 0.35rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def save_result_to_history(data):
    history_item = {
        "request_id": data["request_id"],
        "drug_a": data["drug_a"],
        "drug_b": data["drug_b"],
        "review_status": data["review_status"],
        "summary": data["summary"],
        "full_result": data,
    }
    st.session_state.history.append(history_item)
    st.session_state.history = st.session_state.history[-20:]
    save_history(st.session_state.history)


def apply_pair(drug_a_value, drug_b_value):
    st.session_state.input_drug_a = drug_a_value
    st.session_state.input_drug_b = drug_b_value


def swap_pair():
    st.session_state.input_drug_a, st.session_state.input_drug_b = (
        st.session_state.input_drug_b,
        st.session_state.input_drug_a,
    )


def load_history_item(full_result):
    st.session_state.latest_result = full_result
    st.session_state.input_drug_a = full_result["drug_a"]
    st.session_state.input_drug_b = full_result["drug_b"]


check_api_health()
inject_custom_css()

with st.sidebar:
    st.markdown("### System")
    if st.session_state.api_status == "Connected":
        st.success("FastAPI connected")
    else:
        st.error("API unavailable")

    st.markdown("### Recent analyses")
    if st.session_state.history:
        for item in reversed(st.session_state.history[-5:]):
            label = f"{item['drug_a']} + {item['drug_b']}"
            st.button(
                label,
                key=f"hist_{item['request_id']}",
                use_container_width=True,
                on_click=load_history_item,
                args=(item["full_result"],),
            )
    else:
        st.caption("No saved analyses yet.")

    st.markdown("### Suggested pairs")
    suggestions = [
        ("ibuprofen", "warfarin"),
        ("aspirin", "clopidogrel"),
        ("metformin", "insulin"),
    ]
    for drug_a, drug_b in suggestions:
        st.button(
            f"{drug_a} + {drug_b}",
            key=f"sugg_{drug_a}_{drug_b}",
            use_container_width=True,
            on_click=apply_pair,
            args=(drug_a, drug_b),
        )

    st.markdown("### Notes")
    st.markdown(
        "<div class='pt-sidebar-note'>Use the sidebar for quick re-runs. The main panel stays focused on the current clinical review and supporting evidence.</div>",
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="pt-header">
        <h1 class="pt-title">PharmaTrace</h1>
        <div class="pt-subtitle">Observable pharmacovigilance triage console</div>
        <div class="pt-disclaimer">
            For research and pharmacovigilance triage only — not medical advice.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='pt-section-label'>New analysis</div>", unsafe_allow_html=True)
st.markdown("<div class='pt-card'>", unsafe_allow_html=True)

with st.form("interaction_form"):
    input_col1, input_col2 = st.columns(2)
    with input_col1:
        drug_a = st.text_input(
            "Drug A",
            placeholder="e.g. ibuprofen",
            key="input_drug_a",
        )
    with input_col2:
        drug_b = st.text_input(
            "Drug B",
            placeholder="e.g. warfarin",
            key="input_drug_b",
        )

    action_col1, action_col2, action_col3 = st.columns([1.2, 1.2, 4])
    with action_col1:
        submitted = st.form_submit_button("Run safety review", use_container_width=True)
    with action_col2:
        swap_clicked = st.form_submit_button(
            "Swap drugs",
            use_container_width=True,
            on_click=swap_pair,
        )

st.markdown("</div>", unsafe_allow_html=True)

if submitted:
    if not drug_a.strip() or not drug_b.strip():
        st.error("Please enter both drug names before running a safety review.")
    else:
        start = time.time()
        try:
            with st.spinner("Retrieving FDA evidence and generating a structured safety review..."):
                response = requests.post(
                    f"{API_URL}/check",
                    json={"drug_a": drug_a, "drug_b": drug_b},
                    timeout=60,
                )
            duration = round(time.time() - start, 2)

            if response.status_code == 200:
                data = response.json()
                data["duration_seconds"] = duration
                st.session_state.latest_result = data
                save_result_to_history(data)
            else:
                st.error(f"Backend error ({response.status_code}): {response.text}")

        except Exception as exc:
            st.error(f"Request failed: {exc}")

result = st.session_state.latest_result

if result:
    style = status_style(result["review_status"])

    st.markdown("<div class='pt-spacer'></div>", unsafe_allow_html=True)
    st.markdown("<div class='pt-section-label'>Current analysis</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="pt-status-card" style="background:{style['bg']}; border:1px solid {style['border']};">
            <div class="pt-status-chip" style="background:{style['accent']}; color:#0B1020;">
                {style['label']}
            </div>
            <p class="pt-status-summary">{result["summary"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        st.markdown(
            f"""
            <div class="pt-metric-card">
                <div class="pt-metric-label">Drug pair</div>
                <div class="pt-metric-value">{result['drug_a']} + {result['drug_b']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with metric_col2:
        st.markdown(
            f"""
            <div class="pt-metric-card">
                <div class="pt-metric-label">Response time</div>
                <div class="pt-metric-value">{result['duration_seconds']}s</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with metric_col3:
        st.markdown(
            f"""
            <div class="pt-metric-card">
                <div class="pt-metric-label">Review status</div>
                <div class="pt-metric-value">{style['label']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    summary_tab, evidence_tab, observability_tab = st.tabs(
        ["Summary", "Evidence", "Observability"]
    )

    with summary_tab:
        st.markdown("### Clinical summary")
        st.write(result["summary"])

        st.markdown("### Limitations")
        for item in result["limitations"]:
            st.write(f"- {item}")

    with evidence_tab:
        evidence = result["evidence"]

        with st.expander(f"{result['drug_a'].title()} warnings", expanded=True):
            st.write(evidence["drug_a_warnings"])

        with st.expander(f"{result['drug_b'].title()} warnings", expanded=True):
            st.write(evidence["drug_b_warnings"])

        with st.expander("Label interactions", expanded=True):
            st.code(evidence["label_interactions"])

        with st.expander("FAERS co-report signal", expanded=False):
            st.metric("Co-reports", evidence["faers_co_report_count"])
            st.caption(
                "Observational signal only. Not proof of causality, incidence, or comparative safety."
            )

    with observability_tab:
        st.markdown("### Audit trail")
        with st.expander("Trace and request details", expanded=False):
            st.write(f"Request ID: `{result['request_id']}`")
            st.write(f"Trace ID: `{result['trace_id']}`")
            st.write("Execution path:")
            st.code(
                "pharmatrace.interaction_review -> pharmatrace.agent_analysis -> "
                "openfda.drug_label_lookup -> openfda.adverse_event_co_report_lookup"
            )

        st.markdown("### Inspect in SigNoz")
        st.write("- End-to-end request latency")
        st.write("- Slow FDA lookups")
        st.write("- Failed or fallback analyses")
        st.write("- Repeated high-latency requests")

else:
    st.markdown("<div class='pt-spacer'></div>", unsafe_allow_html=True)
    st.info("Run your first drug pair analysis to view the current clinical summary, evidence, and observability details.")