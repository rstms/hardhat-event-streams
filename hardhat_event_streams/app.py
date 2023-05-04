# hardhat streams API server

# import databases
import logging
from typing import Dict
from uuid import UUID

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlmodel import Session, SQLModel, create_engine, select

from .apikey import get_api_key
from .schema import (
    ContractAddresses,
    EventStream,
    HistoryOptions,
    HistoryReplayOptions,
    Setting,
    StreamsResponse,
    StreamStatus,
)
from .settings import DATABASE_URL, SQL_ECHO
from .version import __version__

# import sqlalchemy


class APIException(Exception):
    pass


# SQLAlchemy specific code, as with any other app

description = """a functional clone of moralis streams service for a hardhat forked testnet"""

app = FastAPI(
    title="hardhat event streams",
    description=description,
    version=__version__,
    dependencies=[Depends(get_api_key)],
)

log = logging.getLogger(__name__)

engine = create_engine(DATABASE_URL, echo=SQL_ECHO, connect_args=dict(check_same_thread=False))


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
    SQLModel.metadata.create_all(engine)


@app.on_event("shutdown")
async def shutdown_event():
    log.debug("shutdown")


@app.get("create", response_model=StreamsResponse)
async def create_stream(
    request: EventStream,
):
    with Session(engine) as session:
        session.add(request)
        session.commit()
        breakpoint()
        pass

    return StreamsResponse(result=False, detail="unimplemented")


@app.patch("stream/{stream_id}", response_model=StreamsResponse)
def update_stream(stream_id: UUID, request: EventStream):
    """modify a stream"""
    return StreamsResponse(result=False, detail="unimplemented")


@app.delete("stream/{stream_id}", response_model=StreamsResponse)
def delete_stream(params):
    """delete a stream"""
    return StreamsResponse(result=False, detail="unimplemented")


@app.post("stream/{stream_id}/address", response_model=StreamsResponse)
def add_address_to_stream(stream_id: UUID, request: ContractAddresses):
    """add a contract address to a stream"""
    return StreamsResponse(result=False, detail="unimplemented")


@app.delete("stream/{stream_id}/address", response_model=StreamsResponse)
def delete_address_from_stream(stream_id: UUID, request: ContractAddresses):
    """delete a contract address from a stream"""
    return StreamsResponse(result=False, detail="unimplemented")


@app.post("/stream/{stream_id}/status", response_model=StreamsResponse)
def update_stream_status(stream_id: UUID, request: StreamStatus):
    """change a stream status"""
    return StreamsResponse(result=False, detail="unimplemented")


@app.get("/streams", response_model=StreamsResponse)
def get_streams():
    """return a list of streams"""
    return StreamsResponse(result=False, detail="unimplemented")


@app.get("/stream/{stream_id}", response_model=StreamsResponse)
def get_stream(stream_id: UUID):
    return StreamsResponse(result=False, detail="unimplemented")


@app.get("/stream/{stream_id}/addresses", response_model=StreamsResponse)
def get_addresses(stream_id: UUID):
    return StreamsResponse(result=False, detail="unimplemented")


@app.get("/history", response_model=StreamsResponse)
def get_history(options: HistoryOptions):
    """get stream history"""
    return StreamsResponse(result=False, detail="unimplemented")


@app.get("/history/replay", response_model=StreamsResponse)
def replay_history(ids: HistoryReplayOptions):
    """request history replay"""
    return StreamsResponse(result=False, detail="unimplemented")


@app.get("/settings", response_model=Dict)
def get_settings():
    """return global config variables"""
    with Session(engine) as session:
        settings = session.exec(select(Setting)).all()
    return {s.key: s.value for s in settings}


@app.post("/settings", response_model=Dict)
def set_settings(values: Dict):
    """set global config values"""
    with Session(engine) as session:
        for k, v in values.items():
            setting = Setting(key=k, value=v)
            session.add(setting)
        session.commit()
        session.refresh(setting)
    return {setting.key: setting.value}


@app.get("stats", response_model=StreamsResponse)
def get_stats(api_key):
    """return global stats"""
    return StreamsResponse(result=dict(active=True), detail="global stats")


@app.get("stats/{stream_id}", response_model=StreamsResponse)
def get_stats_by_stream_id(stream_id: UUID):
    """return stream stats"""
    return StreamsResponse(result=False, detail="unimplemented")
