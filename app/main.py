import uvicorn
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session

from app.api.main import api_router
from app.core.config import settings
from app.models.social_account import SocialAccount as SocialAccountModel
from app.models.database import get_db

app = FastAPI(
    title="CrossPoster API",
    description="API для управления кросспостингом в социальные сети",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение API роутов
app.include_router(api_router, prefix="/api/v1")

# Создание экземпляра шаблонизатора
templates = Jinja2Templates(directory="app/templates")

# Подключение статических файлов (если они есть)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/accounts")
async def accounts_page(request: Request, db: Session = Depends(get_db)):
    # Получаем все существующие аккаунты из базы данных
    social_accounts = db.query(SocialAccountModel).all()
    
    # Создаем словарь для быстрого поиска подключенных аккаунтов
    connected_platforms = {account.platform for account in social_accounts if account.is_active}
    
    return templates.TemplateResponse("accounts.html", {
        "request": request,
        "connected_platforms": connected_platforms
    })

@app.get("/settings")
async def settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)