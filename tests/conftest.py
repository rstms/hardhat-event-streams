import logging
import os

import pytest
from fastapi.testclient import TestClient
from seven_common.schema import Contract
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from hardhat_event_streams.app import app
from hardhat_event_streams.client import HardhatEventStreams
from hardhat_event_streams.db import CRUD, get_db

GATEWAY_PORT = 8082
WEBHOOK_PORT = 8081

info = logging.info


@pytest.fixture
def api_key():
    return os.environ["API_KEY"]


@pytest.fixture
def webhook_url():
    return f"http://localhost:{WEBHOOK_PORT}/contract/event"


@pytest.fixture(scope="session")
def contracts():
    _contracts = {}
    for name in ["Ethersieve", "Character", "Setting", "Scene", "Memory"]:
        _contracts[name] = Contract.from_registry(name=name)
    yield _contracts


@pytest.fixture
def ethersieve(contracts):
    _ethersieve = contracts["Ethersieve"]
    assert isinstance(_ethersieve, Contract)
    return _ethersieve


@pytest.fixture
def crud():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        with CRUD(session) as db:
            yield db


@pytest.fixture()
def streams(crud):
    def get_test_db():
        return crud

    app.dependency_overrides[get_db] = get_test_db
    with TestClient(app) as client:
        server = HardhatEventStreams(requests=client, url=str(client.base_url))
        streams = server.streams
        yield streams
    app.dependency_overrides.clear()
