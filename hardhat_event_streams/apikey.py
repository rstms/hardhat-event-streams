# dependencies

from fastapi import Depends, HTTPException
from fastapi.security.api_key import APIKeyHeader
from requests import codes

from .settings import API_KEY

api_key_scheme = APIKeyHeader(name="X-API-Key")


def get_api_key(key: str = Depends(api_key_scheme)) -> str:
    if key != str(API_KEY):
        raise HTTPException(status_code=codes.unauthorized, detail="not authenticated")
    return key
