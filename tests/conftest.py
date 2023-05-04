import logging
import os

import pytest
from fastapi.testclient import TestClient
from seven_common import schema

from hardhat_event_streams.app import app
from hardhat_event_streams.server import HardhatStreams

GATEWAY_PORT = 8082
WEBHOOK_PORT = 8081

info = logging.info


@pytest.fixture
def api_key():
    return os.environ["API_KEY"]


@pytest.fixture
def webhook_url():
    return f"http://localhost:{WEBHOOK_PORT}/contract/event"


@pytest.fixture
def ethersieve():
    _ethersieve = schema.Contract.from_registry(name="Ethersieve")
    assert isinstance(_ethersieve, schema.Contract)
    return _ethersieve


@pytest.fixture(scope="session")
def streams():
    info("server fixture startup")
    client = TestClient(app)
    yield HardhatStreams(_requests=client)
    info("server fixture shutdown")
