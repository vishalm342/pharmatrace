import time
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="PharmaTrace",
    page_icon="🔬",
    layout="wide",
)

if "history" not in st.session_state:
    st.session_state.history = []

if "latest_result" not in st.session_state:
    st.session_state.latest_result = None

if "api_status" not in st.session_state:
    st.session_state.api_status = "Unknown"


def check_api_health():
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            st.session_state.api_status = "Connected"
        else:
            st.session_state.api_status = "Unavailable"
    except Exception:
        st.session_state.api_status = "Unavailable"


def status_style(review_status: str):
    mapping = {
        "NEEDS_CLINICAL_REVIEW": ("#f59e0b", "Needs clinical review"),
        "CAUTION_FLAGGED": ("#ef4444", "Caution flagged"),
        "NO_LABEL_SIGNAL_FOUND": ("#22c55e", "No label signal found"),
        "ANALYSIS_UNAVAILABLE": ("#6b7280", "Analysis unavailable"),
    }
    return mapping.get(review_status, ("#6b7280", review_status))


check_api_health()

st.markdown(
    """
    <h1 style='margin-bottom:0;'>🔬 PharmaTrace</h1>
    <p style='margin-top:0.25rem;color:#94a3b8;font-size:1.05rem;'>
        Observable pharmacovigilance triage console
    </p>
    """,
    unsafe_allow_html=True,
)

st.warning(
    "For research and pharmacovigilance triage only — not medical advice."
)

with st.sidebar:
    st.subheader("System")
    if st.session_state.api_status == "Connected":
        st.success("FastAPI connected")
    else:
        st.error("API unavailable")

    st.subheader("Recent analyses")
    if st.session_state.history:
        for item in reversed(st.session_state.history[-5:]):
            st.caption(f"{item['drug_a']} + {item['drug_b']}")
            st.code(item["request_id"], language=None)
    else:
        st.caption("No runs yet.")

    st.subheader("Sample pairs")
    st.caption("Try these in the form:")
    st.write("- ibuprofen + warfarin")
    st.write("- aspirin + clopidogrel")
    st.write("- metformin + insulin")

with st.form("interaction_form"):
    col1, col2 = st.columns(2)
    with col1:
        drug_a = st.text_input("Drug A", placeholder="e.g. ibuprofen")
    with col2:
        drug_b = st.text_input("Drug B", placeholder="e.g. warfarin")

    submitted = st.form_submit_button("Run safety review", use_container_width=True)

if submitted:
    start = time.time()
    try:
        with st.spinner("Retrieving FDA evidence, running AI synthesis, and tracing execution..."):
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
            st.session_state.history.append({
                "request_id": data["request_id"],
                "drug_a": data["drug_a"],
                "drug_b": data["drug_b"],
            })
        else:
            st.error(f"Backend error ({response.status_code}): {response.text}")

    except Exception as exc:
        st.error(f"Request failed: {exc}")

result = st.session_state.latest_result

if result:
    color, label = status_style(result["review_status"])

    st.markdown(
        f"""
        <div style="
            margin-top:1rem;
            padding:1rem 1.25rem;
            border:1px solid {color}55;
            border-left:6px solid {color};
            border-radius:14px;
            background:#111827;
        ">
            <div style="font-size:0.95rem;color:#94a3b8;">Review status</div>
            <div style="font-size:1.5rem;font-weight:700;color:{color};margin-top:0.25rem;">
                {label}
            </div>
            <div style="margin-top:0.75rem;color:#e5e7eb;line-height:1.7;">
                {result["summary"]}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Analysis details")
    meta1, meta2, meta3, meta4 = st.columns(4)
    meta1.metric("Request ID", result["request_id"])
    meta2.metric("Trace ID", result["trace_id"][:10] + "...")
    meta3.metric("Drug Pair", f"{result['drug_a']} + {result['drug_b']}")
    meta4.metric("Response Time", f"{result['duration_seconds']}s")

    tab1, tab2, tab3 = st.tabs(["Safety Summary", "Evidence", "Observability"])

    with tab1:
        st.markdown("#### Summary")
        st.write(result["summary"])

        st.markdown("#### Limitations")
        for item in result["limitations"]:
            st.write(f"- {item}")

    with tab2:
        evidence = result["evidence"]

        st.markdown("#### Drug A warnings")
        st.info(evidence["drug_a_warnings"])

        st.markdown("#### Drug B warnings")
        st.info(evidence["drug_b_warnings"])

        st.markdown("#### Label interactions")
        st.code(evidence["label_interactions"])

        st.markdown("#### FAERS co-report count")
        st.metric("Co-reports", evidence["faers_co_report_count"])
        st.caption(
            "Co-reports are observational signals only. They do not prove causality or comparative safety."
        )

    with tab3:
        st.markdown("#### Trace linkage")
        st.write(f"Trace ID: `{result['trace_id']}`")
        st.write("Expected span flow:")
        st.code(
            "pharmatrace.interaction_review -> pharmatrace.agent_analysis -> "
            "openfda.drug_label_lookup -> openfda.adverse_event_co_report_lookup"
        )

        st.markdown("#### What to inspect in SigNoz")
        st.write("- Request latency")
        st.write("- Failed runs / error rate")
        st.write("- OpenFDA lookup duration")
        st.write("- LLM synthesis latency")