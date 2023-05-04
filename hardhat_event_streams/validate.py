# seven_api Schema object formatter functions

import json
import re
import uuid

from hexbytes import HexBytes

HEX_REGEX = "^0x[0-9a-fA-F]+$"


def validate_json(field_name, value, expected_type, allow_none=True):
    if value:
        # if value is str, parse as json
        if isinstance(value, (str, bytes)):
            value = json.loads(value)

        # type_check the decoded value
        if not isinstance(value, expected_type):
            raise TypeError(f"{field_name}:" f" expected {expected_type} got {type(value)}")

    elif not allow_none:
        raise ValueError(f"{field_name}: missing required value")

    return value


def validate_schema_json(field_name, schema_class, value, allow_none=True):
    if value:
        # if value is str, parse as json
        if isinstance(value, (str, bytes)):
            value = schema_class.parse_raw(value)
        elif isinstance(value, dict):
            value = schema_class.parse_obj(value)
        if not isinstance(value, schema_class):
            raise TypeError(
                f"{field_name}:",
                f" Expected {schema_class}, got {type(value)}",
            )
    elif not allow_none:
        raise ValueError(f"{field_name}: missing required value")
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
