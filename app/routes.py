from fastapi import APIRouter
from app.controllers import health_controller

router = APIRouter()

router.get("/health")(
    health_controller.health_check
)
