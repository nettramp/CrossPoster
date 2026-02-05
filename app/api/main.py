from fastapi import APIRouter

from app.api import users, social_accounts, posts, statistics
from app.api import admin

api_router = APIRouter()
api_router.include_router(users.router)
api_router.include_router(social_accounts.router)
api_router.include_router(posts.router)
api_router.include_router(statistics.router)
api_router.include_router(admin.router)