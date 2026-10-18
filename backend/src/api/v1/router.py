from fastapi import APIRouter

from src.api.v1.endpoints.users import router as users_router

router_v1 = APIRouter()

router_v1.include_router(users_router)