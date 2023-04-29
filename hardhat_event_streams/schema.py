# hardhat event stream schema

from pydantic import BaseModel
from typing import List, Optional

class VBaseModel(BaseModel):
    pass

class TableModel(VBaseModel):
    id: Optional[id] = Field(None, description="row id")

class EventStream(VBaseModel):
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

class ContractEvent(TableModel):
    contract_id: int = Field(None, description="DB id of event source contract")
    event_id: UUID = Field(None, description="unique id for each event update received")
    txn_hash: bytes = Field(None, description="event source transaction hash")
    status: ContractEventStatusEnum = Field(..., description="event processing state")
    data: Dict = Field(..., description="event data as dict")

    def __repr__(self):
        return f"<ContractEvent[{self.id}] {self.status}>"

    @validator("txn_hash")
    def validate_hash(cls, v, field):
        return validate_bytes(cls, field, 32, v)


class ContractEventUpdateBlock(VBaseModel):
    number: Union[int, Any] = Field(..., description="block number")
    hash: Optional[bytes] = Field(None, description="block hash")
    timestamp: Optional[Union[datetime, Any]] = Field(None, description="block timestamp")

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
    txs: List[ContractEventUpdateTransaction] = Field(..., discription="transactions associate with event")
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
        return f"<ContractEventUpdate: confirmed={self.confirmed} logs={len(self.logs)} txs={len(self.txs)} transfers={len(self.nftTransfers)}>"

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
