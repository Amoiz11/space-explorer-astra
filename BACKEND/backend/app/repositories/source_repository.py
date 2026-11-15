from typing import Optional
from sqlalchemy.orm import Session, joinedload
from backend.app.models.models import DataProduct, DataSource

class SourceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, product_id: str) -> Optional[DataProduct]:
        return (
            self.db.query(DataProduct)
            .options(joinedload(DataProduct.source))
            .filter(DataProduct.id == product_id)
            .first()
        )

    def get_by_identifier(self, identifier: str) -> Optional[DataProduct]:
        return (
            self.db.query(DataProduct)
            .options(joinedload(DataProduct.source))
            .filter(DataProduct.product_identifier == identifier)
            .first()
        )
