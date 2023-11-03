"""
Constants for the eth_tools package.
"""

DEFAULT_BLOCK_FIELDS = [
    "number",
    "hash",
    "gasUsed",
    "gasLimit",
    "miner",
    "timestamp",
    "sha3Uncles",
    "difficulty",
    "totalDifficulty",
    "size",
    "extraData",
    "receiptsRoot",
    "stateRoot",
    "transactions_count",
]

ETHERSCAN_TRANSACTION_KEYS = [
    "blockNumber",
    "timeStamp",
    "hash",
    "nonce",
    "blockHash",
    "transactionIndex",
    "from",
    "to",
    "value",
    "gas",
    "gasPrice",
    "isError",
    "txreceipt_status",
    "input",
    "contractAddress",
    "cumulativeGasUsed",
    "gasUsed",
    "confirmations",
]

ETHERSCAN_INTERNAL_TRANSACTION_KEYS = [
    "blockNumber",
    "timeStamp",
    "hash",
    "from",
    "to",
    "value",
    "contractAddress",
    "input",
    "type",
    "gas",
    "gasUsed",
    "traceId",
    "isError",
    "errCode",
]

LOG_FORMAT = "%(asctime)-15s - %(levelname)s - %(message)s"
