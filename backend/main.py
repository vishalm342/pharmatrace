import os
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="PharmaTrace API")

from backend.telemetry import setup_telemetry
tracer = setup_telemetry(app)

@app.get("/health")
def health():
    with tracer.start_as_current_span("health-check"):
        return {"status": "ok", "service": "pharmatrace"}

@app.post("/check")
async def check_interaction(payload: dict):
    from backend.agent import run_agent
    drug_a = payload.get("drug_a")
    drug_b = payload.get("drug_b")
    with tracer.start_as_current_span("drug-interaction-check") as span:
        span.set_attribute("drug.a", drug_a)
        span.set_attribute("drug.b", drug_b)
        result = await run_agent(drug_a, drug_b)
        span.set_attribute("agent.response_length", len(result))
    return {"drug_a": drug_a, "drug_b": drug_b, "analysis": result}