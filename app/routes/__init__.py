from fastapi import APIRouter

from app.routes.login_routes import router as login_router
from app.routes.user_routes import router as user_router
from app.routes.notify_routes import router as notify_router

router = APIRouter()

router.include_router(login_router)
router.include_router(user_router)
router.include_router(notify_router)
