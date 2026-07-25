from typing import Literal
from pydantic import BaseModel, Field, field_validator


class InteractionRequest(BaseModel):
    drug_a: str = Field(
        min_length=2,
        max_length=80,
        description="First drug name, for example ibuprofen",
    )
    drug_b: str = Field(
        min_length=2,
        max_length=80,
        description="Second drug name, for example warfarin",
    )

    @field_validator("drug_a", "drug_b")
    @classmethod
    def clean_drug_name(cls, value: str) -> str:
        cleaned = " ".join(value.strip().split())
        if not cleaned.replace("-", "").replace(" ", "").isalpha():
            raise ValueError("Drug name must contain letters, spaces, or hyphens only")
        return cleaned.lower()


class Evidence(BaseModel):
    drug_a_warnings: str
    drug_b_warnings: str
    label_interactions: str
    faers_co_report_count: int = Field(ge=0)


class InteractionResponse(BaseModel):
    request_id: str
    trace_id: str
    drug_a: str
    drug_b: str
    review_status: Literal[
        "NEEDS_CLINICAL_REVIEW",
        "CAUTION_FLAGGED",
        "NO_LABEL_SIGNAL_FOUND",
        "ANALYSIS_UNAVAILABLE",
    ]
    summary: str
    evidence: Evidence
    limitations: list[str]