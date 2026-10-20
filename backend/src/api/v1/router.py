from fastapi import APIRouter

from src.api.v1.endpoints.users import router as users_router
from src.api.v1.endpoints.events import router as events_router
from src.api.v1.endpoints.expenses import router as expenses_router

router_v1 = APIRouter()

router_v1.include_router(users_router)
router_v1.include_router(events_router)
router_v1.include_router(expenses_router)