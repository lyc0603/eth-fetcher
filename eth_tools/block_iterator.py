"""
Function to iterate over blocks
"""
from typing import Collection

from web3 import Web3
from web3.types import BlockData

from eth_tools.logger import logger


class Block:
    """Wrapper of web3.types.BlockData prodiving a ``transactions_count`` property"""

    def __init__(self, data: BlockData):
        self.data = data

    def __getattr__(self, key):
        if key not in self.data:
            raise AttributeError
        value = self.data[key]
        if hasattr(value, "hex"):
            value = value.hex()
        return value

    @property
    def transactions_count(self):
        return len(self.transactions)

    def __repr__(self):
        return "Block(number={number})".format(**self.data)


class BlockIterator:
    """Iterator over Ethereum blocks
    It will lazily fetch each block from ``start_block`` to ``end_block`` inclusive
    using the provided ``web3`` instance.
    """

    def __init__(
        self,
        web3: Web3,
        start_block: int = None,
        end_block: int = None,
        blocks: Collection[int] = None,
        log_interval: int = None,
    ):
        self.web3 = web3
        if blocks is not None:
            assert (
                start_block is None and end_block is None
            ), "blocks is not compatible with start and end block"
            self._blocks = blocks
        else:
            if start_block is None:
                start_block = 0
            if end_block is None:
                end_block = self.web3.eth.blockNumber
            self._blocks = range(start_block, end_block + 1)

        self.blocks_count = len(self._blocks)
        self._blocks_iter = iter(self._blocks)

        self.log_interval = log_interval
        self._processed_count = 0

    def __len__(self):
        return self.blocks_count

    def __iter__(self):
        logger.info("processing %s blocks", self.blocks_count)
        return self

    @property
    def processed_count(self):
        return self._processed_count

    def __next__(self) -> Block:
        block_number = next(self._blocks_iter)
        self._processed_count += 1
        if self.log_interval and self.processed_count % self.log_interval == 0:
            logger.info("%s/%s", self.processed_count, self.blocks_count)
        block = self.web3.eth.getBlock(block_number)
        return Block(block)
