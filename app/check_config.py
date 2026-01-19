import os
from app.core.config import settings

print("Database URL from settings:", settings.database_url)
print("Database URL from environment:", os.environ.get("DATABASE_URL", "Not set"))

# Проверим, можем ли мы подключиться к базе данных
from sqlalchemy import create_engine
try:
    engine = create_engine(settings.database_url)
    connection = engine.connect()
    result = connection.execute("SELECT 1")
    print("Database connection successful:", result.fetchone())
    connection.close()
except Exception as e:
    print("Database connection failed:", e)