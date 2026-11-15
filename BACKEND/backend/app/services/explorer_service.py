from typing import Optional
from sqlalchemy.orm import Session
from backend.app.repositories.explorer_repository import ExplorerRepository
from backend.app.schemas.explorer import ExplorerResponse, ExplorerDetailResponse
from backend.app.schemas.common import PaginatedResponse

class ExplorerService:
    def __init__(self, db: Session):
        self.repository = ExplorerRepository(db)

    def _to_response(self, e) -> ExplorerResponse:
        res = ExplorerResponse.model_validate(e)
        if res.is_placeholder:
            res.label = "Unknown"
        return res

    def list_explorers(
        self,
        mission_id: Optional[str] = None,
        explorer_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> PaginatedResponse[ExplorerResponse]:
        total = self.repository.count(mission_id=mission_id, explorer_type=explorer_type, status=status)
        explorers = self.repository.get_all(
            mission_id=mission_id,
            explorer_type=explorer_type,
            status=status,
            limit=limit,
            offset=offset
        )
        items = [self._to_response(e) for e in explorers]
        return PaginatedResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(items)) < total,
        )

    def get_explorer(self, explorer_id: str) -> Optional[ExplorerDetailResponse]:
        explorer = self.repository.get_by_id(explorer_id)
        if not explorer:
            return None
        res = ExplorerDetailResponse.model_validate(explorer)
        if res.is_placeholder:
            res.label = "Unknown"
        return res
