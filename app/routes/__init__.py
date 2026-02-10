from fastapi import APIRouter

from app.routes.admin_routes import router as admin_router
from app.routes.courses_routes import router as course_router
from app.routes.discipline_routes import router as discipline_router
from app.routes.login_routes import router as login_router
from app.routes.notify_routes import router as notify_router
from app.routes.student_routes import router as student_router
from app.routes.unity_routes import router as unity_router
from app.routes.user_routes import router as user_router

router = APIRouter()

router.include_router(admin_router)
router.include_router(course_router)
router.include_router(discipline_router)
router.include_router(login_router)
router.include_router(notify_router)
router.include_router(student_router)
router.include_router(unity_router)
router.include_router(user_router)