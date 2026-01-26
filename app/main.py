from fastapi import FastAPI
from app.routes import router
from app import users
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Classificador de Políticas Públicas",
    version="0.1.0"
)

app.include_router(router)
app.include_router(users.router)