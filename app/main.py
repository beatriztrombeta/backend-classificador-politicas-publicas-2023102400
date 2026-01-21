from fastapi import FastAPI
from app.routes import router

app = FastAPI(
    title="Classificador de Políticas Públicas",
    version="0.1.0"
)

app.include_router(router)
