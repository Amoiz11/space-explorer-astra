from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class AssistantQueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="User question to the AI research assistant (maximum 500 characters)."
    )


class CitationResponse(BaseModel):
    source_name: str
    product_id: Optional[str] = None
    url: Optional[str] = None
    label: str
    id: Optional[str] = None
    title: Optional[str] = None
    api_path: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AssistantQueryResponse(BaseModel):
    answer: str
    citations: List[CitationResponse]
    confidence_note: str
    evidence_found: bool
    answer_mode: str  # "llm" or "template"
    llm_fallback_reason: Optional[str] = None
    disclaimers: List[str]

    model_config = ConfigDict(from_attributes=True)
