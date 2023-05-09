from starlette.config import Config
from starlette.datastructures import Secret

config = Config(".env")

DEBUG = config("DEBUG", cast=bool, default=False)
SQL_ECHO = config("SQL_ECHO", cast=bool, default=False)
LOG_LEVEL = config("LOG_LEVEL", cast=str, default="WARNING")
API_KEY = config("API_KEY", cast=Secret)
BIND_ADDRESS = config("BIND_ADDRESS", cast=str, default="0.0.0.0")
PORT = config("PORT", cast=int, default=8892)
GATEWAY_URL = config("GATEWAY_URL", cast=str, default="http://localhost:8891")
WORKERS = config("WORKERS", cast=int, default=1)
DATABASE_FILE = config("DATABASE_FILE", cast=str, default="./streams.db")
DATABASE_URL = config("DATABASE_URL", cast=str, default=f"sqlite:///{DATABASE_FILE}")
