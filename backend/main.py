import uuid
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from opentelemetry.trace import Status, StatusCode

from backend.agent import run_agent
from backend.schemas import InteractionRequest, InteractionResponse
from backend.telemetry import setup_telemetry

app = FastAPI(
    title="PharmaTrace API",
    version="1.0.0",
    description="Observable pharmacovigilance triage API.",
)

tracer = setup_telemetry(app)


@app.get("/health")
def health():
    return {"status": "ok", "service": "pharmatrace"}


@app.post("/check", response_model=InteractionResponse)
async def check_interaction(payload: InteractionRequest):
    request_id = f"pt_{uuid.uuid4().hex[:8]}"

    with tracer.start_as_current_span("pharmatrace.interaction_review") as span:
        span.set_attribute("pharmatrace.request_id", request_id)
        span.set_attribute("pharmatrace.drug_a", payload.drug_a)
        span.set_attribute("pharmatrace.drug_b", payload.drug_b)

        try:
            result = await run_agent(payload.drug_a, payload.drug_b)
            trace_id = format(span.get_span_context().trace_id, "032x")

            return InteractionResponse(
                request_id=request_id,
                trace_id=trace_id,
                drug_a=payload.drug_a,
                drug_b=payload.drug_b,
                review_status=result["review_status"],
                summary=result["summary"],
                evidence=result["evidence"],
                limitations=[
                    "For research and pharmacovigilance triage only — not medical advice.",
                    "FDA adverse-event co-reports do not establish causality, incidence, or comparative safety.",
                    "A qualified clinician must review patient-specific medication decisions.",
                ],
            )

        except Exception as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, "interaction analysis failed"))
            span.set_attribute("error.type", type(exc).__name__)
            raise HTTPException(
                status_code=502,
                detail="PharmaTrace could not complete the analysis. Please retry.",
            ) from exc