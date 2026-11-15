from typing import List, Dict, Any
from ai.retrieval import EvidenceItem


def format_citations(evidence_items: List[EvidenceItem]) -> List[Dict[str, Any]]:
    """
    Format citation metadata directly from retrieved evidence.
    Citations strictly originate from approved database and document evidence,
    never from model-generated text.
    """
    citations = []
    seen = set()

    for item in evidence_items:
        key = (item.source_name, item.product_id)
        if key in seen:
            continue
        seen.add(key)

        label = "Unknown" if item.is_placeholder else item.label

        citation = {
            "source_name": item.source_name,
            "product_id": item.product_id,
            "url": item.url,
            "label": label,
            "id": item.product_id or item.source_name,
            "title": item.source_name,
            "api_path": item.url,
        }
        citations.append(citation)

    return citations
