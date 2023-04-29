# hardhat streams API client

import os

import requests

DEFAULT_GATEWAY = "http://localhost:8892"


class HardhatEventBase:
    url = os.environ["HARDHAT_EVENTS_GATEWAY", DEFAULT_GATEWAY]

    def post(self, api_key, path, **kwargs):
        return self.request(requests.post, path, **kwargs)

    def patch(self, api_key, path, **kwargs):
        return self.request(requests.patch, path, **kwargs)

    def delete(self, api_key, path, **kwargs):
        return self.request(requests.delete, path, **kwargs)

    def get(self, api_key, path, **kwargs):
        return self.request(requests.get, path, **kwargs)

    def request(self, api_key, func, path, **kwargs):
        paged = kwargs.pop("paged", False)
        kwargs["headers"] = {"x-api-key": api_key, "content-type": "application/json"}
        return self.check(func(self.url + path, **kwargs), paged)

    def check(self, response, paged):
        response.raise_for_status()
        result = response.json()
        ret = dict(result=result)
        if paged:
            ret.update(dict(cursor="", total=len(result)))
        return ret


class HardhatEventStreams(HardhatEventBase):
    def __init__(self, url=None):
        super().init(url)

    def create_stream(self, api_key, body):
        """create a stream"""
        return self.post(api_key, "/create", json=body)

    def update_stream(self, api_key, params, body):
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


class HardhatEventsHistory(HardhatEventBase):
    def get_history(self, api_key, params):
        """get stream history"""
        options = dict(exclude_payload=params["excludePayload"])
        return self.get(api_key, "/history", paged=True, json=options)

    def replay_history(self, api_key, params):
        """request history replay"""
        ids = dict(stream=params["streamId"], history=params["id"])
        return self.post(api_key, "/history/replay", paged=True, json=ids)


class HardhatEventsProject(HardhatEventBase):
    def get_settings(self, api_key):
        """return global config variables"""
        return self.get(api_key, "/settings")

    def set_settings(self, api_key, body):
        """set a global config variable"""
        return self.post(api_key, "/settings", json=body)


class HardhatEventsStats(HardhatEventBase):
    def get_stats(self, api_key):
        """return global stats"""
        return self.get(api_key, "/stats")

    def get_stats_by_stream_id(self, api_key, params):
        """return stream stats"""
        stream_id = params["id"]
        return self.get(api_key, f"stats/{stream_id}")