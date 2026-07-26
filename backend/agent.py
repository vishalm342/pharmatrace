import json
import os

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from opentelemetry import trace

from backend.tools import check_interaction, lookup_drug

tracer = trace.get_tracer("pharmatrace.agent")

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)

SYSTEM_PROMPT = """
You are PharmaTrace, a pharmacovigilance triage assistant.

Your job is to summarize supplied FDA label evidence. You are not a clinician and
must not diagnose, prescribe, or claim a drug combination is safe.

Return VALID JSON only. No markdown. No code fence.

Use exactly this schema:
{
  "review_status": "NEEDS_CLINICAL_REVIEW" | "CAUTION_FLAGGED" | "NO_LABEL_SIGNAL_FOUND",
  "summary": "Two or three factual sentences based only on the supplied evidence."
}

Rules:
- Choose NEEDS_CLINICAL_REVIEW if warnings or interaction text indicates bleeding,
  contraindications, severe reactions, or important uncertainty.
- Choose CAUTION_FLAGGED if evidence contains a relevant caution but no clear severe signal.
- Choose NO_LABEL_SIGNAL_FOUND only when FDA label evidence contains no relevant warning.
- FAERS co-report counts are observational signals, not proof of causality or risk.
- Never say "safe", "unsafe", "low risk", "moderate risk", or "high risk".
"""


def _fallback_summary(drug_a: str, drug_b: str) -> dict:
    return {
        "review_status": "ANALYSIS_UNAVAILABLE",
        "summary": (
            f"Automated synthesis was unavailable for {drug_a} and {drug_b}. "
            "Review the returned FDA label evidence with a qualified clinician."
        ),
    }


async def run_agent(drug_a: str, drug_b: str) -> dict:
    with tracer.start_as_current_span("pharmatrace.agent_analysis") as span:
        span.set_attribute("pharmatrace.drug_a", drug_a)
        span.set_attribute("pharmatrace.drug_b", drug_b)
        span.set_attribute("gen_ai.system", "groq")
        span.set_attribute("gen_ai.request.model", "llama-3.3-70b-versatile")

        drug_a_data = lookup_drug(drug_a)
        drug_b_data = lookup_drug(drug_b)
        interaction_data = check_interaction(drug_a, drug_b)

        evidence = {
            "drug_a_warnings": drug_a_data["warnings"],
            "drug_b_warnings": drug_b_data["warnings"],
            "label_interactions": (
                f"{drug_a.title()} label: {drug_a_data['interactions']}\n\n"
                f"{drug_b.title()} label: {drug_b_data['interactions']}"
            ),
            "faers_co_report_count": interaction_data["faers_co_report_count"],
        }

        prompt_data = {
            "drug_a": drug_a,
            "drug_b": drug_b,
            "evidence": evidence,
        }

        try:
            response = llm.invoke([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        "Analyze this evidence and return JSON only:\n"
                        f"{json.dumps(prompt_data)}"
                    )
                ),
            ])
            print("\n--- GROQ RAW RESPONSE ---")
            print(response.content)
            print("--- END GROQ RESPONSE ---\n")

            parsed = json.loads(response.content)
            review_status = parsed.get("review_status", "NEEDS_CLINICAL_REVIEW")
            summary = parsed.get(
                "summary",
                "FDA evidence was retrieved. A qualified clinician should review it.",
            )

            if review_status not in {
                "NEEDS_CLINICAL_REVIEW",
                "CAUTION_FLAGGED",
                "NO_LABEL_SIGNAL_FOUND",
            }:
                review_status = "NEEDS_CLINICAL_REVIEW"

        except (json.JSONDecodeError, ValueError, Exception) as exc:
            span.record_exception(exc)
            span.set_attribute("error.type", type(exc).__name__)
            fallback = _fallback_summary(drug_a, drug_b)
            review_status = fallback["review_status"]
            summary = fallback["summary"]

        span.set_attribute("pharmatrace.review_status", review_status)
        span.set_attribute(
            "pharmatrace.faers_co_report_count",
            evidence["faers_co_report_count"],
        )

        return {
            "review_status": review_status,
            "summary": summary,
            "evidence": evidence,
        }