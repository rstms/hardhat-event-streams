# custom json class

# subclass json encoder to support json dump of bytes and datetime elements

import datetime
import json
from decimal import Decimal
from uuid import UUID

from eth_utils import to_hex
from hexbytes import HexBytes


class Encoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        if isinstance(o, HexBytes):
            return to_hex(bytes(o))
        if isinstance(o, datetime.datetime):
            return o.isoformat(" ")[:19]
        elif isinstance(o, datetime.date):
            return o.isoformat()
        elif isinstance(o, datetime.time):
            return o.isoformat()[:8]
        elif isinstance(o, bytes):
            return to_hex(o)
        elif isinstance(o, UUID):
            return str(o)

        return super().default(o)


def load(*args, **kwargs):
    return json.load(*args, **kwargs)


def dump(*args, **kwargs):
    kwargs.update({"cls": Encoder})
    return json.dump(*args, **kwargs)


def loads(*args, **kwargs):
    return json.loads(*args, **kwargs)


def dumps(*args, **kwargs):
    kwargs.update({"cls": Encoder})
    return json.dumps(*args, **kwargs)
