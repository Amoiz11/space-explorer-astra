from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login")
def login():
    return {"message": "Auth will be implemented in Phase 3", "is_placeholder": True}

@router.get("/me")
def get_current_user():
    return {"user": None, "is_placeholder": True}
