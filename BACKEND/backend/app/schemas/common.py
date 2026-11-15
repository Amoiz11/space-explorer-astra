from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    limit: int
    offset: int
    has_more: bool

class ErrorResponse(BaseModel):
    error: str
    detail: str
    status_code: int
    is_placeholder: bool = False
