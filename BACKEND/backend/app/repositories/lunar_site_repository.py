from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.models import CandidateLandingSite

class LunarSiteRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, body_id: Optional[str] = None) -> List[CandidateLandingSite]:
        query = self.db.query(CandidateLandingSite)
        if body_id:
            query = query.filter(CandidateLandingSite.body_id == body_id)
        return query.all()

    def get_by_id(self, site_id: str) -> Optional[CandidateLandingSite]:
        return self.db.query(CandidateLandingSite).filter(CandidateLandingSite.id == site_id).first()

    def create(self, site_data: dict) -> CandidateLandingSite:
        site = CandidateLandingSite(**site_data)
        self.db.add(site)
        self.db.commit()
        self.db.refresh(site)
        return site

    def update(self, site_id: str, update_data: dict) -> Optional[CandidateLandingSite]:
        site = self.get_by_id(site_id)
        if not site:
            return None
        for key, value in update_data.items():
            if value is not None:
                setattr(site, key, value)
        self.db.commit()
        self.db.refresh(site)
        return site

    def delete(self, site_id: str) -> bool:
        site = self.get_by_id(site_id)
        if not site:
            return False
        self.db.delete(site)
        self.db.commit()
        return True
