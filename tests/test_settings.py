from logging import info
from pprint import pformat


def test_settings_set(api_key, streams):
    ret = streams.project.set_settings(api_key, {"region": "us-east-1"})
    assert ret
    info(pformat(ret))


def test_settings_get(api_key, streams):
    ret = streams.project.get_settings(api_key)
    assert ret
    info(pformat(ret))
