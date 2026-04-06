from fastapi import APIRouter
from app.api.v1.endpoints import equipment, submittals

api_router = APIRouter()
api_router.include_router(equipment.router)
api_router.include_router(submittals.router)
