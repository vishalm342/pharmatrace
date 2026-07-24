import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

def setup_telemetry(app):
    resource = Resource.create({
        "service.name": os.getenv("OTEL_SERVICE_NAME", "pharmatrace"),
        "service.version": "1.0.0",
    })

    exporter = OTLPSpanExporter(
        endpoint=f"{os.getenv('SIGNOZ_ENDPOINT')}/v1/traces",
        headers={"signoz-ingestion-key": os.getenv("SIGNOZ_INGESTION_KEY")},
    )

    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()

    return trace.get_tracer("pharmatrace")