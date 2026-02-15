from fastapi import APIRouter
from .customer_profile import router as customer_profile_router
from .sales_script import router as sales_script_router

api_router = APIRouter()

api_router.include_router(
    customer_profile_router,
    prefix="/presale/ai",
    tags=["Customer Profile"]
)

api_router.include_router(
    sales_script_router,
    prefix="/presale/ai",
    tags=["Sales Script"]
)

__all__ = ["api_router"]
