from logging import info
from pprint import pformat

from seven_common.streams import EventStream


def test_streams_create(api_key, streams, ethersieve, webhook_url):
    event_stream = EventStream.from_contract(ethersieve, webhook_url)
    body = event_stream.dict(exclude={"id", "status", "statusMessage"})
    ret = streams.evm_streams.create_stream(api_key, body=body)
    assert ret
    info(pformat(ret))
