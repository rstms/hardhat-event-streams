# hardhat streams API client


import databases
import sqlalchemy
from pydantic import BaseModel
from fastapi import FastAPI

# SQLAlchemy specific code, as with any other app
DATABASE_URL = "sqlite:///./test.db"

from .version import __version__

DEFAULT_GATEWAY = "http://localhost:8892"

description = """a functional clone of moralis streams service for a hardhat forked testnet"""

app = FastAPI(
    title='hardhat event streams',
    description=description,
    version=__version__,
    dependencies=[Depends(get_api_key)],
)

log = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def system_exception_handler(request: Request, exc: Exception):
    message = f"{exc.__class__.__name__}: {'; '.join([str(arg) for arg in exc.args])} (see error log for traceback)"
    if isinstance(exc, APIException):
        code = 422
    else:
        code = 500
    log.error(message)
    return JSONResponse(status_code=code, content={"detail": message})


@app.on_event("startup")
async def startup_event():
    log.debug('startup')

@app.on_event("shutdown")
async def shutdown_event():
    log.debug("shutdown")

@app.get("/create")
async def create_stream(
    request: EventStream,
):
    log.debug("--> /create {request}")

    log.debug(f"<-- {result}")
    return result

@app.patch("/stream/{stream_id}")
def update_stream(self, stream_id, request: ):
    """modify a stream"""
    stream_id = params["id"]
    return self.patch(api_key, f"/stream/{stream_id}", json=body)

def delete_stream(self, api_key, params):
    """delete a stream"""
    stream_id = params["id"]
    return self.delete(api_key, f"/stream/{stream_id}")

def _addreses(self, body):
    address = body["address"]
    if not isinstance(address, list):
        address = [address]
    return dict(addresses=address)

def add_address_to_stream(self, api_key, params, body):
    """add a contract address to a stream"""
    stream_id = params["id"]
    return self.post(api_key, f"/stream/{stream_id}/address", json=self._addresses(body))

def delete_address_from_stream(self, api_key, params, body):
    """delete a contract address from a stream"""
    stream_id = params["id"]
    return self.delete(api_key, f"/stream/{stream_id}/address", json=self._addresses(body))

def update_stream_status(self, api_key, params, body):
    """change a stream status"""
    stream_id = params["id"]
    status = dict(status=body["status"])
    return self.post(api_key, f"/stream/{stream_id}/status", json=status)

def get_streams(self, api_key, params):
    """return a list of streams"""
    return self.get(api_key, "/streams", paged=True)

def get_stream(self, api_key, params):
    """return a specific stream"""
    stream_id = params["id"]
    return self.get(api_key, f"/stream/{stream_id}")

def get_addresses(self, api_key, params):
    """return list of stream addresses"""
    stream_id = params["id"]
    return self.get(api_key, f"/stream/{stream_id}/addresses")

def get_history(self, api_key, params):
    """get stream history"""
    options = dict(exclude_payload=params["excludePayload"])
    return self.get(api_key, "/history", paged=True, json=options)

def replay_history(self, api_key, params):
    """request history replay"""
    ids = dict(stream=params["streamId"], history=params["id"])
    return self.post(api_key, "/history/replay", paged=True, json=ids)

def get_settings(self, api_key):
    """return global config variables"""
    return self.get(api_key, "/settings")

def set_settings(self, api_key, body):
    """set a global config variable"""
    return self.post(api_key, "/settings", json=body)

def get_stats(self, api_key):
    """return global stats"""
    return self.get(api_key, "/stats")

def get_stats_by_stream_id(self, api_key, params):
    """return stream stats"""
    stream_id = params["id"]
    return self.get(api_key, f"stats/{stream_id}")
