from fastapi import APIRouter
from backend.app.api.v1 import (
    bodies,
    missions,
    rovers,
    locations,
    trajectories,
    images,
    telemetry,
    analytics,
    assistant,
    sources,
    lunar_sites,
    auth,
    admin,
    map_layers,
    lunar_products,
    lunar_compare,
)

api_router = APIRouter()

# API v1 Status
@api_router.get("/status", tags=["Status"])
def get_api_status():
    return {
        "status": "online",
        "api_version": "v1",
        "message": "Space Explorer API v1 is active",
        "is_placeholder": False,
    }

# Include modular routers
api_router.include_router(bodies.router)
api_router.include_router(missions.router)
api_router.include_router(rovers.router)
api_router.include_router(locations.router)
api_router.include_router(trajectories.router)
api_router.include_router(images.router)
api_router.include_router(telemetry.router)
api_router.include_router(analytics.router)
api_router.include_router(assistant.router)
api_router.include_router(sources.router)
api_router.include_router(lunar_sites.router)
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(map_layers.router)
api_router.include_router(lunar_products.router)
api_router.include_router(lunar_compare.router)
