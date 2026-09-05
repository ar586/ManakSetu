from fastapi import APIRouter
from app.api.v1.endpoints import search, standards

api_router = APIRouter()

api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(standards.router, prefix="/standards", tags=["standards"])
