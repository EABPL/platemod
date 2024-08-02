from fastapi import APIRouter
from app.api.endpoints import platemod

api_router = APIRouter()
api_router.include_router(platemod.router, prefix="/v1", tags=["platemod"])