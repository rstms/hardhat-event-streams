# seven_api Schema object formatter functions

import re
import uuid

from hexbytes import HexBytes

from . import json

HEX_REGEX = "^0x[0-9a-fA-F]+$"


def validate_json(field_name, value, expected_type, allow_none=True):
    """given a json string or the expected type, return a json string"""
    if value is None:
        if not allow_none:
            raise ValueError(f"{field_name}: missing required value")
    elif isinstance(value, expected_type):
        # if value is in expected type, return JSON dump
        pass
    elif isinstance(value, str):
        # if value is str, decode as JSON and type_check
        value = json.loads(value)
        if not isinstance(value, expected_type):
            raise TypeError(f"{field_name}:" f" expected {expected_type} got {type(value)}")
    return value


def _handle_bytes(value):
    try:
        # pydantic munges strings into bytes, so
        # see if the string decodes into valid hexadecimal;
        # interpret it that way if it does
        if re.match(HEX_REGEX, value.decode()):
            value = bytes(HexBytes(value.decode()))
    except UnicodeDecodeError:
        pass
    return value


def validate_bytes(cls, field, length, value, allow_none=False):
    _value = value
    if value:
        if isinstance(value, bytes):
            value = _handle_bytes(value)
        elif isinstance(value, HexBytes):
            value = bytes(value)
        else:
            raise TypeError(
                f"{cls.__name__}.{field.name}:",
                f" Expected {length} bytes, got {repr(_value)}",
            )
    elif not allow_none:
        raise ValueError(f"{cls.__name__}.{field.name}: missing required value")

    if value and length and len(value) != length:
        raise ValueError(
            f"{cls.__name__}.{field.name}:",
            f" Expected {length} bytes, got {len(_value)}",
        )

    return value


def validate_uuid(cls, field, value, allow_none=False):
    if value in [None, ""]:
        if allow_none:
            value = None
        else:
            raise ValueError(f"{cls.__name__}.{field.name}: missing required value")
    elif isinstance(value, uuid.UUID):
        pass
    elif isinstance(value, str):
        value = uuid.UUID(value)
    elif isinstance(value, bytes):
        value = uuid.UUID(value.decode())
    else:
        raise TypeError(
            f"{field.name}:",
            f" Expected UUID, got {repr(value)}",
        )
    return value
