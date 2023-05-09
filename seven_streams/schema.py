# hardhat event stream schema

import enum
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from eth_utils import humanize_bytes, humanize_hash
from hexbytes import HexBytes
from pydantic import AnyUrl
from pydantic import BaseModel as _BaseModel
from pydantic import root_validator, validator
from sqlmodel import JSON, Column, Field
from sqlmodel import SQLModel as _SQLModel

from . import json
from .validate import validate_bytes, validate_json, validate_uuid


class EventStreamsEnum(enum.Enum):
    @classmethod
    def values(cls):
        return [m.value for m in cls.__members__.values()]


class EventStreamsStatusEnum(EventStreamsEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    TERMINATED = "terminated"


class EventStreamsRegionEnum(EventStreamsEnum):
    US_EAST_1 = "us-east-1"
    US_WEST_2 = "us-west-2"
    EU_CENTRAL_1 = "eu-central-1"
    AP_SOUTHEAST_1 = "ap-southeast-1"


class ContractEventTypeEnum(EventStreamsEnum):
    TOKEN_TRANSFER = "TOKEN_TRANSFER"
    EVENT_RECORDED = "EVENT_RECORDED"


class BaseModel(_BaseModel):
    class Config:
        json_loads = json.loads
        use_enum_values = True
        json_encoders = {
            "bytes": lambda b: HexBytes(b).hex() if len(b) else "",
            "AnyUrl": lambda u: str(u),
            "UUID": lambda u: str(u),
        }

        arbitary_types_allowed = True


class SQLModel(BaseModel, _SQLModel):
    pass


class AddressBase(SQLModel):
    address: bytes = Field(..., description="contract address")

    @validator("address")
    def validate_address(cls, v, field):
        return validate_bytes(cls, field, 20, v)


class Address(AddressBase, table=True):
    id: Optional[int] = Field(None, primary_key=True)


class AddressMapBase(SQLModel):
    address_id: int = Field(..., description="contract ID", foreign_key="address.id")
    stream_id: int = Field(..., description="stream ID", foreign_key="eventstream.id")


class AddressMap(AddressMapBase, table=True):
    id: Optional[int] = Field(None, primary_key=True)


class AddressRequest(BaseModel):
    address: List[bytes] = Field(..., description="address or list of addresses")

    @validator("address")
    def validate_address_list(cls, v, field):
        if not isinstance(v, (list, tuple)):
            v = [v]
        ret = [validate_bytes(cls, field, 20, _v) for _v in v]
        return ret


class AddressResponse(AddressRequest):
    streamId: UUID = Field(..., description="ID of associated stream")

    @validator("streamId")
    def validate_stream_id(cls, v, field):
        ret = validate_uuid(cls, field, v)
        return ret


class HistoryOptions(BaseModel):
    excludePayload: bool = Field(True, description="exclude payload from results if True")
    id: UUID = Field(..., description="requested history id")


class HistoryReplayOptions(BaseModel):
    streamId: UUID = Field(..., description="stream for which history is requested")
    id: UUID = Field(..., description="requested history id")


class StreamStatus(BaseModel):
    status: EventStreamsStatusEnum = Field(..., description="stream status value")


class SettingBase(SQLModel):
    key: str = Field(..., description="setting name", index=True)
    value: str = Field(..., description="setting value")


class Setting(SettingBase, table=True):
    id: Optional[int] = Field(None, primary_key=True)


class JSONList(JSON):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        return validate_json("JSONList", v, list)

    @classmethod
    def __modify_schema(cls, field_schema):
        field_schema.update(type="string", example='[{"key": "value"}]')


class JSONDict(JSON):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        ret = validate_json("JSONDict", v, dict)
        return ret

    @classmethod
    def __modify_schema(cls, field_schema):
        field_schema.update(type="string", example='{"key": "value"}')


class EventStreamBase(SQLModel):
    webhookUrl: AnyUrl = Field(..., description="event receiver webhook URL")
    description: Optional[str] = Field("", description="user-defined identifier string")
    tag: Optional[str] = Field("", description="client identifier for event notification stream")
    topic0: JSONList = Field(
        ...,
        sa_column=Column(JSON),
        description="An Array of topic0’s in string-signature format ex: [‘FunctionName(address,uint256)’]",
    )
    allAddresses: Optional[bool] = Field(False, description="request events for all addresses matching ABI and topic0")
    includeNativeTxs: Optional[bool] = Field(True, description="request native transaction events")
    includeContractLogs: Optional[bool] = Field(True, description="include logs of contract interactions")
    includeInternalTxs: Optional[bool] = Field(True, description="request internal transaction events")
    includeAllTxLogs: bool = Field(
        True, description="include all logs if at least one value in tx or log matches stream config"
    )
    getNativeBalances: Optional[JSONList] = Field(
        "[]", sa_column=Column(JSON), description="Include native balances matching trigger filter"
    )
    chainIds: JSONList = Field(
        ..., sa_column=Column(JSON), description="The ids of the chains for this stream in hex Ex: ['0x1','0x38']"
    )
    abi: List[JSONDict] = Field(..., sa_column=Column(JSON), description="list of event abi JSON strings")
    demo: bool = Field(False, description="request demo mode")
    triggers: Optional[JSONList] = Field(
        "[]",
        sa_column=Column(JSON),
        description="list of json strings describing trigger objects (see moralis streams docs)",
    )
    advancedOptions: Optional[JSONList] = Field(
        "[]",
        sa_column=Column(JSON),
        description="list of json strings describing  advanced options (see moralis streams docs)",
    )
    status: Optional[str] = Field("", description="Status Word")
    statusMessage: Optional[str] = Field("", description="Detailed Status")
    streamId: Optional[UUID] = Field(None, description="stream identifier GUID")

    @validator("streamId")
    def validate_stream_id(cls, v, field):
        ret = validate_uuid(cls, field, v, allow_none=True)
        return ret

    def __repr__(self):
        return f"<EventStream: {str(self.streamId)} tag={self.tag} {self.webhookUrl}>"


class EventStream(EventStreamBase, table=True):
    id: Optional[int] = Field(None, primary_key=True)


class StreamResponse(EventStreamBase):
    id: UUID = Field(..., description="UUID stream ID")

    def __repr__(self):
        return f"<Stream: {str(self.id)} tag={self.tag} {self.webhookUrl}>"

    def __str__(self):
        return repr(self)

    @root_validator(pre=True)
    def id_validator(cls, values):
        values["id"] = values["streamId"]
        return values


class ContractEventBase(SQLModel):
    contract_address: bytes = Field(None, description="address of event source contract")
    event_hash: bytes = Field(None, description="event hash")
    txn_hash: bytes = Field(None, description="event source transaction hash")
    data: JSONDict = Field(..., sa_column=Column(JSON), description="event data as json")

    def __repr__(self):
        return f"<ContractEvent[{self.id}] {self.status}>"

    @validator("contract_address")
    def validate_address(cls, v, field):
        return validate_bytes(cls, field, 20, v)

    @validator("txn_hash", "event_hash")
    def validate_hash(cls, v, field):
        return validate_bytes(cls, field, 32, v)

    @validator("data")
    def validate_data(cls, v, field):
        return validate_json("data", v, dict)


class ContractEvent(ContractEventBase, table=True):
    id: Optional[int] = Field(None, primary_key=True)


class EventResponse(BaseModel):
    status: str = Field(..., description="status message")
    count: int = Field(..., description="record count")


class ContractEventUpdateBlock(BaseModel):
    number: Union[int, Any] = Field(..., description="block number")
    hash: Optional[bytes] = Field(None, description="block hash")
    timestamp: Union[datetime, Any, None] = Field(None, description="block timestamp")

    @validator("number")
    def validate_number(cls, v, field):
        return int(v or "0")

    @validator("hash")
    def validate_hash(cls, v, field):
        return validate_bytes(cls, field, 32, v, allow_none=True)

    @validator("timestamp")
    def validate_timestamp(cls, v, field):
        return v or None

    def __repr__(self):
        return f"block={humanize_hash(self.hash or b'')}"


class ContractEventUpdateLog(BaseModel):
    logIndex: int = Field(..., description="log index in block")
    transactionHash: bytes = Field(..., description="hash of transaction emitting event")
    address: bytes = Field(..., description="address of contract emitting event")
    data: Union[bytes, None] = Field(..., description="event data")
    topic0: bytes = Field(..., description="event topic0")
    topic1: bytes = Field(..., description="event topic1")
    topic2: bytes = Field(..., description="event topic2")
    topic3: bytes = Field(..., description="event topic3")

    @validator("transactionHash", "topic0", "topic1", "topic2", "topic3")
    def validate_hash(cls, v, field):
        return validate_bytes(cls, field, 32, v)

    @validator("address")
    def validate_address(cls, v, field):
        return validate_bytes(cls, field, 20, v)

    @validator("data")
    def validate_variable_bytes(cls, v, field):
        return validate_bytes(cls, field, 0, v, allow_none=True)

    def __repr__(self):
        return f"<log: contract={humanize_bytes(self.address)} txn={humanize_hash(self.transactionHash)}>"


class ContractEventUpdateTransaction(BaseModel):
    hash: bytes = Field(None, description="transaction hash (32 bytes)")
    gas: int = Field(None, description="gas limit")
    gasPrice: int = Field(None, description="gas price")
    nonce: int = Field(..., ge=0, description="transaction nonce")
    input: Optional[bytes] = Field(None, description="input data")
    transactionIndex: int = Field(..., description="index of transaction")
    fromAddress: bytes = Field(None, description="from address")
    toAddress: bytes = Field(None, description="from address")
    value: int = Field(..., ge=0, description="transaction value")
    type: int = Field(..., description="transaction type")
    v: int = Field(None, ge=0, description="signature recovery value v")
    r: bytes = Field(None, description="signature ecdsa r value")
    s: bytes = Field(None, description="signature ecdsa s value")
    receiptCumulativeGasUsed: int = Field(..., description="cumulative gas used in mined txn block")
    receiptGasUsed: int = Field(..., description="gas used by transaction")
    receiptContractAddress: Optional[bytes] = Field(None, description="address of deployed transaction")
    root: Optional[bytes] = Field(None, description="Pre-Byzantium transaction root field")
    receiptStatus: int = Field(..., description="transaction status: 1=success, 0=reverted")

    @validator("hash")
    def validate_hash(cls, v, field):
        return validate_bytes(cls, field, 32, v)

    @validator("receiptContractAddress", "fromAddress", "toAddress")
    def validate_optional_address(cls, v, field):
        return validate_bytes(cls, field, 20, v, allow_none=True)

    @validator("input", "r", "s", "root")
    def validate_variable_bytes(cls, v, field):
        return validate_bytes(cls, field, 0, v, allow_none=True)

    def __repr__(self):
        return f"<txn: hash={humanize_hash(self.hash)}>"


class ContractEventUpdateInternalTransaction(BaseModel):
    from_address: bytes = Field(..., description="from address of transaction")
    to_address: bytes = Field(..., description="to address of transaction")
    value: int = Field(..., description="value transferred by transacition in WEI")
    gas: int = Field(..., description="gas used by transaction")
    transactionHash: bytes = Field(..., description="transaction hash")

    @root_validator(pre=True)
    def validate_internal_txn(cls, values):
        for key in "to", "from":
            if key in values:
                values[key + "_address"] = values.pop(key)
        return values

    @validator("transactionHash")
    def validate_hash(cls, v, field):
        return validate_bytes(cls, field, 32, v)

    @validator("from_address", "to_address")
    def validate_address(cls, v, field):
        return validate_bytes(cls, field, 20, v)

    def __repr__(self):
        return f"<internal_txn: hash={humanize_hash(self.transactionHash)}>"


class ContractEventUpdate(BaseModel):
    abi: List[Dict] = Field(..., description="ABI of contract emitting event")
    block: ContractEventUpdateBlock = Field(..., description="block containing transaction emitting event")
    chainId: Optional[bytes] = Field(None, description="stream chain id")
    confirmed: Optional[bool] = Field(None, description="event block has been confirmed")
    erc20Approvals: List[Dict] = Field(..., description="ERC20 approval data")
    erc20Transfers: List[Dict] = Field(..., description="ERC20 transfer data")
    logs: List[ContractEventUpdateLog] = Field(..., description="event log data")
    nftApprovals: Dict[str, List[Dict]] = Field(..., description="ERC721 or ERC1155 approval data")
    nftTransfers: List[Dict] = Field(..., description="ERC721 or ERC1155 transfer data")
    retries: Optional[int] = Field(None, description="number of event notification retries")
    streamId: Union[UUID, Any] = Field(..., description="ID of stream delivering event notification")
    tag: Union[str, Any] = Field(..., description="client identifier for event notification stream")
    txs: List[ContractEventUpdateTransaction] = Field(..., description="transactions associate with event")
    txsInternal: List[ContractEventUpdateInternalTransaction] = Field(
        ..., description="internal transactions associated with event"
    )

    @root_validator(pre=True)
    def validate_contract_event_update(cls, values):
        for txs in values.get("txsInternal", {}):
            for key in "to", "from":
                if key in txs:
                    txs[key + "_address"] = txs.pop(key)
        return values

    @validator("tag")
    def validate_tag(cls, v, field):
        return v or None

    @validator("chainId")
    def validate_bytes(cls, v, field):
        return validate_bytes(cls, field, 0, v, allow_none=True) or None

    @validator("streamId")
    def validate_stream_id(cls, v, field):
        return validate_uuid(cls, field, v, allow_none=True)

    def __repr__(self):
        return (
            "<ContractEventUpdate:"
            f" confirmed={self.confirmed}"
            f" logs={len(self.logs)}"
            f" txs={len(self.txs)}"
            f" transfers={len(self.nftTransfers)}>"
        )

    def has_payload(self):
        return any(
            (
                self.erc20Approvals,
                self.erc20Transfers,
                self.logs,
                self.nftApprovals["ERC1155"],
                self.nftApprovals["ERC721"],
                self.nftTransfers,
                self.txs,
                self.txsInternal,
            )
        )
