from logging import info
from pprint import pformat

import pytest


@pytest.fixture
def setting():
    return {"region": "us-east-1"}


def test_settings_set(api_key, streams, setting):
    ret = streams.project.set_settings(api_key, setting)
    assert ret
    info(pformat(ret))


def test_settings_get(api_key, streams, setting):
    before = streams.project.get_settings(api_key)
    ret = streams.project.set_settings(api_key, setting)
    after = streams.project.get_settings(api_key)

    assert before == {}
    assert ret == setting
    assert after == setting

    info(pformat(ret))
