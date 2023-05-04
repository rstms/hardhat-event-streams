# hardhat event stream schema

import enum
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from eth_utils import humanize_bytes, humanize_hash
from pydantic import BaseModel, root_validator, validator
from sqlmodel import Field, SQLModel

from .validate import validate_bytes, validate_uuid


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


class VBaseModel(BaseModel):
    pass


class StreamsResponse(VBaseModel):
    result: Any = Field(True, description="return data")
    cursor: str = Field("", description="paging cursor")
    total: int = Field(None, description="total number of results")


class ContractAddresses(VBaseModel):
    addresses: List[str] = Field(..., description="list of contract addresses")


class HistoryOptions(VBaseModel):
    excludePayload: bool = Field(True, description="exclude payload from results if True")


class HistoryReplayOptions(VBaseModel):
    streamId: UUID = Field(..., description="stream for which history is requested")
    id: UUID = Field(..., description="requested history id")


class StreamStatus(VBaseModel):
    status: EventStreamsStatusEnum = Field(..., description="stream status value")


class SettingBase(SQLModel):
    key: str = Field(..., description="setting name", index=True)
    value: str = Field(..., description="setting value")


class Setting(SettingBase, table=True):
    id: Optional[int] = Field(None, primary_key=True)


class EventStream(SQLModel):
    webhookUrl: str = Field(..., description="event receiver webhook URL")
    description: Optional[str] = Field("", description="user-defined identifier string")
    tag: Optional[str] = Field("", description="client identifier for event notification stream")
    topic0: List[str] = Field(
        ..., description="An Array of topic0’s in string-signature format ex: [‘FunctionName(address,uint256)’]"
    )
    allAddresses: Optional[bool] = Field(False, description="request events for all addresses matching ABI and topic0")
    includeNativeTxs: Optional[bool] = Field(True, description="request native transaction events")
    includeContractLogs: Optional[bool] = Field(True, description="include logs of contract interactions")
    includeInternalTxs: Optional[bool] = Field(True, description="request internal transaction events")
    includeAllTxLogs: bool = Field(
        True, description="include all logs if at least one value in tx or log matches stream config"
    )
    getNativeBalances: Optional[List[str]] = Field([], description="Include native balances matching trigger filter")
    abi: List[Dict] = Field(..., description="contract abi")
    advancedOptions: Optional[List[Any]] = Field([], description="advanced options (see moralis streams docs)")
    chainIds: List[str] = Field(..., description="The ids of the chains for this stream in hex Ex: ['0x1','0x38']")
    demo: bool = Field(False, description="request demo mode")
    triggers: Optional[List[Any]] = Field([], description="trigger objects (see moralis streams docs)")

    def __repr__(self):
        return f"<EventStream: tag={self.tag} {self.webhookUrl}>"


class ContractEvent(SQLModel):
    contract_id: int = Field(None, description="DB id of event source contract")
    event_id: UUID = Field(None, description="unique id for each event update received")
    txn_hash: bytes = Field(None, description="event source transaction hash")
    event_type: ContractEventTypeEnum = Field(..., description="type of event")
    data: Dict = Field(..., description="event data as dict")

    def __repr__(self):
        return f"<ContractEvent[{self.id}] {self.status}>"

    @validator("txn_hash")
    def validate_hash(cls, v, field):
        return validate_bytes(cls, field, 32, v)


class ContractEventUpdateBlock(VBaseModel):
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


class ContractEventUpdateLog(VBaseModel):
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
    def validate_topic(cls, v, field):
        return validate_bytes(cls, field, 20, v)

    @validator("data")
    def validate_variable_bytes(cls, v, field):
        return validate_bytes(cls, field, 0, v, allow_none=True)

    def __repr__(self):
        return f"<log: contract={humanize_bytes(self.address)} txn={humanize_hash(self.transactionHash)}>"


class ContractEventUpdateTransaction(VBaseModel):
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


class ContractEventUpdateInternalTransaction(VBaseModel):
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


class ContractEventUpdate(VBaseModel):
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
