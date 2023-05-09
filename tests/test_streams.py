from logging import info
from pprint import pformat
from uuid import uuid4

import pytest
from eth_utils import is_same_address
from seven_common.streams import EventStream

from hardhat_event_streams import HardhatStreamsError
from hardhat_event_streams.schema import AddressResponse


@pytest.fixture
def create_stream(streams, api_key):
    def _create_stream(contract, tag, webhook_url):
        event_stream = EventStream.from_contract(contract, webhook_url, tag=tag)
        body = event_stream.dict(exclude={"id", "status", "statusMessage"})
        ret = streams.evm_streams.create_stream(api_key, body=body)
        return EventStream(**ret)

    return _create_stream


@pytest.fixture
def stream_result():
    def _stream_result(ret):
        result = ret["result"]
        if isinstance(result, list):
            return [EventStream(**e) for e in result]
        else:
            return EventStream(**result)

    return _stream_result


@pytest.fixture
def labels():
    return set(["spam", "eggs", "dimsdale", "spiny-norman"])


@pytest.fixture
def create_stream_set(streams, api_key, ethersieve, webhook_url, create_stream, stream_result):
    def _create_stream_set(labels):
        assert len(set(labels)) == len(labels)
        for tag in labels:
            create_stream(ethersieve, tag, webhook_url)
        stream_set = stream_result(streams.evm_streams.get_streams(api_key, params=dict(limit=100, cursor="")))
        return stream_set

    return _create_stream_set


@pytest.fixture
def get_streams(streams, api_key, stream_result):
    def _get_streams():
        return stream_result(streams.evm_streams.get_streams(api_key, params=dict(limit=100, cursor="")))

    return _get_streams


def test_streams_create(streams, api_key, ethersieve, webhook_url, create_stream, stream_result):
    before = stream_result(streams.evm_streams.get_streams(api_key, params=dict(limit=100, cursor="")))
    new_stream = create_stream(ethersieve, "test_create", webhook_url)
    after = stream_result(streams.evm_streams.get_streams(api_key, params=dict(limit=100, cursor="")))
    assert isinstance(new_stream, EventStream)
    assert not before
    assert after
    assert len(after) == 1
    assert new_stream.id == after[0].id
    info(new_stream)
    info(pformat(after))


def test_streams_get(streams, api_key, get_streams, labels, create_stream_set, stream_result):
    before = stream_result(streams.evm_streams.get_streams(api_key, params=dict(limit=100, cursor="")))
    assert not before
    create_stream_set(labels)
    streams = get_streams()
    stream_tags = set([stream.tag for stream in streams])
    assert labels == stream_tags
    for stream in streams:
        info(stream)


def test_streams_delete_one(streams, api_key, create_stream_set, get_streams, stream_result):
    kniggits = ["arthur", "lancelot", "robin"]
    create_stream_set(kniggits)
    assert len(get_streams()) == len(kniggits)
    before = {stream.tag: stream for stream in get_streams()}
    stream_id = before["lancelot"].id
    ret = EventStream(**streams.evm_streams.delete_stream(api_key, params=dict(id=stream_id)))
    assert isinstance(ret, EventStream)
    assert ret.tag == "lancelot"
    assert ret.id == stream_id

    after = {stream.tag: stream for stream in get_streams()}
    assert len(before) == 3
    assert len(after) == 2
    assert set(list(after.keys())) == set(["arthur", "robin"])


def test_streams_delete_nonexistent(streams, api_key, create_stream_set, get_streams, stream_result):
    kniggits = ["arthur", "lancelot", "robin"]
    create_stream_set(kniggits)
    before = get_streams()
    stream_id = str(uuid4())
    with pytest.raises(HardhatStreamsError):
        ret = EventStream(**streams.evm_streams.delete_stream(api_key, params=dict(id=stream_id)))
        assert ret
    after = get_streams()
    assert len(before) == 3
    assert len(after) == 3


def test_streams_addresses(streams, api_key, contracts, create_stream, webhook_url, stream_result):
    character_address = contracts["Character"].address
    scene_address = contracts["Scene"].address

    # create a stream with the Character contract
    stream = create_stream(contracts["Character"], "character", webhook_url)

    # check that it originally has no addresses
    ret = streams.evm_streams.get_addresses(api_key, params=dict(id=stream.id))
    response = AddressResponse(**ret)
    assert isinstance(response, AddressResponse)
    assert response.address == []

    # add the Character contract address
    params = dict(id=stream.id)
    body = dict(address=[character_address])
    ret = streams.evm_streams.add_address_to_stream(api_key, params=params, body=body)
    response = AddressResponse(**ret)
    assert isinstance(response, AddressResponse)
    assert str(response.streamId) == stream.id
    assert isinstance(response.address, list)

    # verify the response contains the address
    assert len(response.address) == 1
    assert is_same_address(character_address, response.address[0])

    # check that get_addresses shows the Character address
    ret = streams.evm_streams.get_addresses(api_key, params=dict(id=stream.id))
    response = AddressResponse(**ret)
    assert isinstance(response, AddressResponse)
    assert str(response.streamId) == stream.id
    assert isinstance(response.address, list)
    assert len(response.address) == 1
    assert is_same_address(character_address, response.address[0])

    # add the Scene address to the stream
    params = dict(id=stream.id)
    body = dict(address=[scene_address])
    ret = streams.evm_streams.add_address_to_stream(api_key, params=params, body=body)
    response = AddressResponse(**ret)
    assert isinstance(response.address, list)
    assert str(response.streamId) == stream.id
    assert len(response.address) == 1
    assert is_same_address(scene_address, response.address[0])

    def _check_addresses(response):
        assert isinstance(response, AddressResponse)
        assert str(response.streamId) == stream.id
        assert isinstance(response.address, list)
        assert len(response.address) == 2
        character_found = False
        scene_found = False
        for address in response.address:
            if is_same_address(address, character_address):
                character_found = True
            elif is_same_address(address, scene_address):
                scene_found = True
        assert scene_found
        assert character_found

    # check that get_addresses shows both Character and Scene addresses
    ret = streams.evm_streams.get_addresses(api_key, params=dict(id=stream.id))
    response = AddressResponse(**ret)
    _check_addresses(response)

    # delete both addreses from the stream
    params = dict(id=stream.id)
    body = dict(address=[character_address, scene_address])
    ret = streams.evm_streams.delete_address_from_stream(api_key, params=params, body=body)
    response = AddressResponse(**ret)
    _check_addresses(response)

    # delete the stream
    params = dict(id=stream.id)
    ret = streams.evm_streams.delete_stream(api_key, params=params)
    deleted_stream = EventStream(**ret)
    assert isinstance(deleted_stream, EventStream)
    assert deleted_stream.id == stream.id

    # query the streams, ensure empty list returned
    ret = streams.evm_streams.get_streams(api_key, params=dict(limit=100, cursor=""))
    assert isinstance(ret, dict)
    result = stream_result(ret)
    assert isinstance(result, list)
    assert result == []
