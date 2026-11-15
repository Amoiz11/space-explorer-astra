from typing import Optional
from sqlalchemy.orm import Session
from backend.app.repositories.body_repository import BodyRepository
from backend.app.schemas.body import CelestialBodyResponse
from backend.app.schemas.common import PaginatedResponse

class BodyService:
    def __init__(self, db: Session):
        self.repository = BodyRepository(db)

    def list_bodies(self, limit: int = 50, offset: int = 0) -> PaginatedResponse[CelestialBodyResponse]:
        total = self.repository.count()
        items = self.repository.get_all(limit=limit, offset=offset)
        res_items = [CelestialBodyResponse.model_validate(b) for b in items]
        return PaginatedResponse(
            items=res_items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(res_items)) < total,
        )

    def get_body(self, body_id: str) -> Optional[CelestialBodyResponse]:
        body = self.repository.get_by_id(body_id)
        if not body:
            return None
        return CelestialBodyResponse.model_validate(body)
