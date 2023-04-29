from pathlib import Path

from starlette.config import Config
from starlette.datastructures import Secret

API_KEY = config("HARDHAT_STREAMS_API_KEY", cast=Secret)
BIND_ADDRESS = config("BIND_ADDRESS", cast=str, default="0.0.0.0")
PORT = config("PORT", cast=str, default="8892")
GATEWAY_ADDRESS = config("BIND_ADDRESS", cast=str, default="0.0.0.0")
GATEWAY_PORT = config("PORT", cast=str, default="8891")
