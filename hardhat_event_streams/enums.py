# seven_api enums

import enum

class EventStreamsEnum(enum.Enum):
    @classmethod
    def values(cls):
        return [m.value for m in cls.__members__.values()]

class EventStreamsStatusEnum(APIEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    TERMINATED = "terminated"


class EventStreamsRegionEnum(APIEnum):
    US_EAST_1 = "us-east-1"
    US_WEST_2 = "us-west-2"
    EU_CENTRAL_1 = "eu-central-1"
    AP_SOUTHEAST_1 = "ap-southeast-1"
