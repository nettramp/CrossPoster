import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings

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

@app.get("/")
async def root():
    return {"message": "CrossPoster API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)