import httpx
from opentelemetry import trace

tracer = trace.get_tracer("pharmatrace.tools")

FDA_LABEL_URL = "https://api.fda.gov/drug/label.json"
FDA_EVENT_URL = "https://api.fda.gov/drug/event.json"


def _first_section(label: dict, key: str, fallback: str) -> str:
    values = label.get(key, [])
    if not values:
        return fallback
    return values[0][:900]


def lookup_drug(drug_name: str) -> dict:
    with tracer.start_as_current_span("openfda.drug_label_lookup") as span:
        span.set_attribute("pharmatrace.drug_name", drug_name)

        try:
            with httpx.Client(timeout=12) as client:
                response = client.get(
                    FDA_LABEL_URL,
                    params={
                        "search": f'openfda.brand_name:"{drug_name}"',
                        "limit": 1,
                    },
                )
                response.raise_for_status()

            results = response.json().get("results", [])
            if not results:
                span.set_attribute("pharmatrace.label_found", False)
                return {
                    "name": drug_name,
                    "found": False,
                    "warnings": "No FDA label found for this drug name.",
                    "interactions": "No FDA label interaction section found.",
                }

            label = results[0]
            span.set_attribute("pharmatrace.label_found", True)

            return {
                "name": drug_name,
                "found": True,
                "warnings": _first_section(
                    label,
                    "warnings",
                    "No warnings section returned by the FDA label.",
                ),
                "interactions": _first_section(
                    label,
                    "drug_interactions",
                    "No drug-interactions section returned by the FDA label.",
                ),
            }

        except httpx.HTTPError as exc:
            span.record_exception(exc)
            span.set_attribute("error.type", type(exc).__name__)
            return {
                "name": drug_name,
                "found": False,
                "warnings": "FDA label lookup is temporarily unavailable.",
                "interactions": "FDA label lookup is temporarily unavailable.",
            }


def check_interaction(drug_a: str, drug_b: str) -> dict:
    with tracer.start_as_current_span("openfda.adverse_event_co_report_lookup") as span:
        span.set_attribute("pharmatrace.drug_a", drug_a)
        span.set_attribute("pharmatrace.drug_b", drug_b)

        query = (
            f'patient.drug.medicinalproduct:"{drug_a}"'
            f'+AND+patient.drug.medicinalproduct:"{drug_b}"'
        )

        try:
            with httpx.Client(timeout=12) as client:
                response = client.get(
                    FDA_EVENT_URL,
                    params={"search": query, "limit": 1},
                )

            if response.status_code == 404:
                count = 0
            else:
                response.raise_for_status()
                count = response.json().get("meta", {}).get("results", {}).get("total", 0)

            span.set_attribute("pharmatrace.faers_co_report_count", count)

            return {
                "drug_a": drug_a,
                "drug_b": drug_b,
                "faers_co_report_count": count,
            }

        except httpx.HTTPError as exc:
            span.record_exception(exc)
            span.set_attribute("error.type", type(exc).__name__)
            return {
                "drug_a": drug_a,
                "drug_b": drug_b,
                "faers_co_report_count": 0,
            }