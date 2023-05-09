# hardhat event streams

"""functional clone of moralis streams service for a hardhat forked testnet"""

from .cli import cli
from .client import HardhatStreamsError, streams
from .version import __version__

__all__ = ["cli", "__version__", "streams", "HardhatStreamsError"]
