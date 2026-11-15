from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/status")
def get_admin_status():
    return {"admin_status": "active", "is_placeholder": True}
