import shlex

import pytest
from click.testing import CliRunner
from hardhat_event_streams.cli import cli


@pytest.fixture
def runner():
    def _runner(*args, **kwargs):
        if isinstance(args[0], str):
            args = tuple(shlex.split(args[0]))
        result = CliRunner().invoke(cli, *args, **kwargs)
        assert result
        return result

    return _runner


def test_cli_help(runner):
    runner("--help")
