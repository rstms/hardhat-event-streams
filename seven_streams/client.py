# hardhat streams API client

import logging
import os

import httpx

from . import schema

DEFAULT_GATEWAY = "http://localhost:8892"

logger = logging.getLogger(__name__)


class HardhatStreamsError(Exception):
    pass


class HardhatStreamsBase:
    def __init__(self, url=None, requests=None):
        self.url = url or os.environ.get("HARDHAT_EVENTS_GATEWAY", DEFAULT_GATEWAY)
        self.requests = requests or httpx

    def __repr__(self):
        return f"<{self.__class__.__name__} {hex(id(self))}>"

    def post(self, api_key, path, **kwargs):
        return self.request(api_key, self.requests.post, path, **kwargs)

    def patch(self, api_key, path, **kwargs):
        return self.request(api_key, self.requests.patch, path, **kwargs)

    def delete(self, api_key, path, **kwargs):
        return self.request(api_key, self.requests.delete, path, **kwargs)

    def get(self, api_key, path, **kwargs):
        return self.request(api_key, self.requests.get, path, **kwargs)

    def request(self, api_key, func, path, **kwargs):
        paged = kwargs.pop("paged", False)
        kwargs["headers"] = {"x-api-key": api_key, "content-type": "application/json"}
        response = func(self.url + path, **kwargs)
        return self.check(response, paged)

    def check(self, response, paged):
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            msg = f"{response} {response.text}"
            logger.exception(msg)
            raise HardhatStreamsError(msg)
        result = response.json()
        if paged:
            result = dict(result=result, cursor="", total=len(result))
        return result


class HardhatEventsStreams(HardhatStreamsBase):
    def create_stream(self, api_key, body):
        """create a stream"""
        stream = schema.EventStream(**body)
        return self.post(api_key, "/stream", content=stream.json())

    def update_stream(self, api_key, params, body):
        """modify a stream"""
        stream_id = params["id"]
        stream = schema.EventStream(**body)
        stream.streamId = stream_id
        return self.patch(api_key, f"/stream/{stream_id}", content=stream.json())

    def delete_stream(self, api_key, params):
        """delete a stream"""
        stream_id = params["id"]
        return self.post(api_key, f"/stream/{stream_id}/delete")

    def _addresses(self, body):
        address = body["address"]
        if not isinstance(address, list):
            address = [address]
        return schema.AddressRequest(address=address)

    def add_address_to_stream(self, api_key, params, body):
        """add a contract address to a stream"""
        stream_id = params["id"]
        request = self._addresses(body)
        return self.post(api_key, f"/stream/{stream_id}/add_address", content=request.json())

    def delete_address_from_stream(self, api_key, params, body):
        """delete a contract address from a stream"""
        stream_id = params["id"]
        request = self._addresses(body)
        return self.post(api_key, f"/stream/{stream_id}/delete_address", content=request.json())

    def update_stream_status(self, api_key, params, body):
        """change a stream status"""
        stream_id = params["id"]
        request = schema.StreamStatus(status=body["status"])
        return self.post(api_key, f"/stream/{stream_id}/status", content=request.json())

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


class HardhatEventsHistory(HardhatStreamsBase):
    def get_history(self, api_key, params):
        """get stream history"""
        options = dict(exclude_payload=params["excludePayload"])
        return self.get(api_key, "/history", paged=True, json=options)

    def replay_history(self, api_key, params):
        """request history replay"""
        ids = dict(stream=params["streamId"], history=params["id"])
        return self.post(api_key, "/history/replay", paged=True, json=ids)


class HardhatEventsProject(HardhatStreamsBase):
    def get_settings(self, api_key):
        """return global config variables"""
        return self.get(api_key, "/settings")

    def set_settings(self, api_key, body):
        """set a global config variable"""
        return self.post(api_key, "/settings", json=body)


class HardhatEventsStats(HardhatStreamsBase):
    def get_stats(self, api_key):
        """return global stats"""
        return self.get(api_key, "/stats")

    def get_stats_by_stream_id(self, api_key, params):
        """return stream stats"""
        stream_id = params["id"]
        return self.get(api_key, f"stats/{stream_id}")


class HardhatStreams:
    def __init__(self, url, requests):
        self.evm_streams = HardhatEventsStreams(url, requests)
        self.history = HardhatEventsHistory(url, requests)
        self.project = HardhatEventsProject(url, requests)
        self.stats = HardhatEventsStats(url, requests)


class HardhatEventStreams:
    def __init__(self, url=None, requests=None):
        self.streams = HardhatStreams(url, requests)


streams = HardhatEventStreams()
