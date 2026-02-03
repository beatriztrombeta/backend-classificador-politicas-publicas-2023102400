from fastapi import FastAPI
from dotenv import load_dotenv
from app.routes import router

load_dotenv()

app = FastAPI(
    title="Classificador de Políticas Públicas",
    version="0.1.0"
)

app.include_router(router)