from typing import Optional
from sqlalchemy.orm import Session
from backend.app.repositories.source_repository import SourceRepository
from backend.app.schemas.source import SourceProvenanceResponse, DataSourceInfo

class SourceService:
    def __init__(self, db: Session):
        self.repository = SourceRepository(db)

    def get_provenance(self, product_id: str) -> Optional[SourceProvenanceResponse]:
        product = self.repository.get_by_id(product_id)
        if not product:
            product = self.repository.get_by_identifier(product_id)

        if not product:
            return None

        is_placeholder = bool(product.is_placeholder)
        # Rule: a placeholder can never return a label other than "Unknown"
        label = "Unknown" if is_placeholder else (product.label or "Unknown")

        source_info = DataSourceInfo(
            id=product.source.id if product.source else "unknown-source",
            name=product.source.name if product.source else "Unknown NASA Archive Source",
            source_url=product.source.source_url if product.source else None,
            organization=product.source.organization if product.source else None,
            is_placeholder=product.source.is_placeholder if product.source else True,
        )

        return SourceProvenanceResponse(
            product_id=product.id,
            product_identifier=product.product_identifier,
            version=product.version,
            checksum=product.checksum,
            source=source_info,
            observation_time=product.observation_time,
            retrieved_at=product.retrieved_at,
            coordinate_frame=product.coordinate_frame,
            units=product.units,
            processing_method=product.processing_method,
            uncertainty=product.uncertainty,
            label=label,
            is_placeholder=is_placeholder,
        )
