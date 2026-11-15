from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.services.subresource_service import SubresourceService
from backend.app.schemas.subresources import TrajectoryResponse

router = APIRouter(prefix="/rovers", tags=["Trajectories"])

@router.get("/{rover_id}/trajectory", response_model=TrajectoryResponse)
def get_rover_trajectory(
    rover_id: str,
    db: Session = Depends(get_db)
):
    service = SubresourceService(db)
    trajectory = service.get_trajectory(rover_id)
    if not trajectory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validated trajectory for rover '{rover_id}' not found"
        )
    return trajectory
