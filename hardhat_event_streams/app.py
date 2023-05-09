# hardhat streams API server

# import databases
import logging
from typing import Dict, List
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .apikey import get_api_key
from .db import CRUD, get_db, init_db
from .schema import (
    Address,
    AddressMap,
    AddressRequest,
    AddressResponse,
    ContractEvent,
    EventResponse,
    EventStream,
    HistoryOptions,
    HistoryReplayOptions,
    Setting,
    StreamResponse,
    StreamStatus,
)
from .version import __version__


class APIException(Exception):
    pass


description = """a functional clone of moralis streams service for a hardhat forked testnet"""

app = FastAPI(
    title="hardhat event streams",
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
    log.debug("startup")
    init_db()


@app.on_event("shutdown")
async def shutdown_event():
    log.debug("shutdown")


@app.post("/stream", response_model=StreamResponse)
async def create_stream(request: EventStream, db: CRUD = Depends(get_db)):
    request.status = "created"
    request.statusMessage = "stream is created"
    request.streamId = uuid4()
    request.id = None
    stream = db.create(request)
    response = StreamResponse(**stream.dict())
    logging.info(f"created {response}")
    return response


def _get_stream(db, stream_id):
    stream = db.read_one(EventStream, EventStream.streamId == stream_id, allow_none=True)
    if not stream:
        raise HTTPException(status_code=404, detail=f"stream {stream_id} does not exist")
    return stream


@app.patch("/stream", response_model=StreamResponse)
async def update_stream(request: EventStream, db: CRUD = Depends(get_db)):
    """modify a stream"""
    stream = _get_stream(db, request.streamId)
    request.id = stream.id
    request.statusMessage = "stream is updated"
    updated = db.update(request)
    response = StreamResponse(**updated.dict())
    logging.info(f"updated {response}")
    return response


@app.post("/stream/{stream_id}/delete", response_model=StreamResponse)
async def delete_stream(stream_id: UUID, db: CRUD = Depends(get_db)):
    """delete a stream"""
    stream = _get_stream(db, stream_id)
    db.delete(stream)
    stream.status = "deleted"
    stream.statusMessage = "stream is deleted"
    address_ids = [
        map.address_id for map in db.read_all(AddressMap, AddressMap.stream_id == stream.id, allow_none=True)
    ]
    db.delete(AddressMap, AddressMap.stream_id == stream.id, allow_none=True)
    delete_if_unmapped(db, address_ids)
    response = StreamResponse(**stream.dict())
    logging.info(f"deleted {response}")
    return response


@app.post("/stream/{stream_id}/add_address", response_model=AddressResponse)
async def add_address_to_stream(stream_id: UUID, request: AddressRequest, db: CRUD = Depends(get_db)):
    """add a contract address to a stream"""
    stream = _get_stream(db, stream_id)
    addresses = []
    for address in request.address:
        address = db.upsert(Address(address=address))
        db.upsert(AddressMap(stream_id=stream.id, address_id=address.id))
        addresses.append(address.address)
    response = AddressResponse(streamId=stream.streamId, address=addresses)
    return response


def delete_if_unmapped(db, address_ids):
    for address_id in address_ids:
        maps = db.read(AddressMap, AddressMap.address_id == address_id, allow_none=True)
        if not maps:
            db.delete(Address, Address.id == address_id, allow_none=True)


@app.post("/stream/{stream_id}/delete_address", response_model=AddressResponse)
async def delete_address_from_stream(stream_id: UUID, request: AddressRequest, db: CRUD = Depends(get_db)):
    """delete a contract address from a stream"""
    stream = _get_stream(db, stream_id)
    addresses = []
    for address in request.address:
        address = db.read_one(Address, Address.address == address)
        db.delete(AddressMap, AddressMap.stream_id == stream.id, AddressMap.address_id == address.id, allow_none=True)
        delete_if_unmapped(db, [address.id])
        addresses.append(address.address)
    response = AddressResponse(streamId=stream.streamId, address=addresses)
    return response


@app.post("/stream/{stream_id}/status", response_model=StreamResponse)
async def update_stream_status(stream_id: UUID, request: StreamStatus, db: CRUD = Depends(get_db)):
    """change a stream status"""
    stream = _get_stream(db, stream_id)
    old_status = stream.status
    stream.status = request.status
    stream.statusMessage = f"status changed from {old_status} to {stream.status}"
    stream = db.update(stream)
    response = StreamResponse(**stream.dict())
    logging.info(f"updated {response} status to {stream.status}")
    return response


@app.get("/streams", response_model=List[StreamResponse])
async def get_streams(db: CRUD = Depends(get_db)):
    """return a list of streams"""
    streams = db.read(EventStream)
    response = [StreamResponse(**stream.dict()) for stream in streams]
    for stream in response:
        logging.info(f"{stream}")
    return response


@app.get("/stream/{stream_id}", response_model=StreamResponse)
async def get_stream(stream_id: UUID, db: CRUD = Depends(get_db)):
    stream = _get_stream(db, stream_id)
    response = StreamResponse(**stream.dict())
    logging.info(f"{response}")
    return response


@app.get("/stream/{stream_id}/addresses", response_model=AddressResponse)
async def get_addresses(stream_id: UUID, db: CRUD = Depends(get_db)):
    stream = _get_stream(db, stream_id)
    maps = db.read_all(AddressMap, AddressMap.stream_id == stream.id, allow_none=True)
    addresses = [db.read_one(Address, Address.id == map.address_id) for map in maps]
    response = AddressResponse(streamId=stream.streamId, address=[address.address for address in addresses])
    return response


@app.get("/history", response_model=List[Dict])
async def get_history(options: HistoryOptions, db: CRUD = Depends(get_db)):
    """get stream history"""
    return []


@app.get("/history/replay", response_model=List[Dict])
async def replay_history(ids: HistoryReplayOptions, db: CRUD = Depends(get_db)):
    """request history replay"""
    return []


@app.get("/settings", response_model=Dict)
async def get_settings(db: CRUD = Depends(get_db)):
    """return global config variables"""
    settings = db.read_all(Setting)
    return {s.key: s.value for s in settings}


@app.post("/settings", response_model=Dict)
async def set_settings(values: Dict, db: CRUD = Depends(get_db)):
    """set global config values"""
    settings = {}
    for k, v in values.items():
        db.upsert(Setting(key=k, value=v))
        settings[k] = v
    return settings


@app.get("/stats", response_model=Dict)
async def get_stats(db: CRUD = Depends(get_db)):
    """return global stats"""
    return dict(stats=True)


@app.get("/stats/{stream_id}", response_model=Dict)
async def get_stats_by_stream_id(stream_id: UUID, db: CRUD = Depends(get_db)):
    """return stream stats"""
    stream = _get_stream(db, stream_id)
    return dict(streamId=stream_id, stats=True, index=stream.id)


@app.post("/event", response_model=EventResponse)
def post_event(event: ContractEvent, db: CRUD = Depends(get_db)):
    event = db.create(event)
    return dict(status="received", count=1)


@app.get("/events", response_model=List[ContractEvent])
def get_events(db: CRUD = Depends(get_db)):
    return db.read_all(ContractEvent)


@app.get("/event/<event_id>", response_model=ContractEvent)
def get_event(event_id: int, db: CRUD = Depends(get_db)):
    return db.read_one(ContractEvent, ContractEvent.id == event_id)


@app.delete("/events", response_model=EventResponse)
def delete_events(db: CRUD = Depends(get_db)):
    deleted = db.delete(ContractEvent, ContractEvent.id >= 0)
    return EventResponse(status="deleted", count=deleted)


@app.delete("/event/<event_id>", response_model=EventResponse)
def delete_event(event_id: int, db: CRUD = Depends(get_db)):
    deleted = db.delete(ContractEvent, ContractEvent.id == event_id)
    return EventResponse(status="deleted", count=deleted)
