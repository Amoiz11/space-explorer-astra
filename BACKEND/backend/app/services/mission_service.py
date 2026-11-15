from typing import Optional
from sqlalchemy.orm import Session
from backend.app.repositories.mission_repository import MissionRepository
from backend.app.schemas.mission import MissionResponse
from backend.app.schemas.common import PaginatedResponse

class MissionService:
    def __init__(self, db: Session):
        self.repository = MissionRepository(db)

    def _to_response(self, m) -> MissionResponse:
        res = MissionResponse.model_validate(m)
        if res.is_placeholder:
            res.label = "Unknown"
        return res

    def list_missions(
        self,
        body_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> PaginatedResponse[MissionResponse]:
        total = self.repository.count(body_id=body_id, status=status)
        missions = self.repository.get_all(body_id=body_id, status=status, limit=limit, offset=offset)
        items = [self._to_response(m) for m in missions]
        return PaginatedResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(items)) < total,
        )

    def get_mission(self, mission_id: str) -> Optional[MissionResponse]:
        mission = self.repository.get_by_id(mission_id)
        if not mission:
            return None
        return self._to_response(mission)
