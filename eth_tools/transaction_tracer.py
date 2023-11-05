"""
Function to trace a transaction.
"""

from web3 import Web3
from retry import retry

from eth_tools.logger import logger


class TransactionTracer:
    """
    class to trace a transaction
    """

    def __init__(self, web3: Web3):
        self.web3 = web3

    # retry is a decorator to retry a function if it fails
    # delay is the delay between each retry
    # backoff is the factor by which the delay increases after each retry
    # tries is the number of times to retry
    @retry(delay=1, backoff=2, tries=3, logger=logger)
    def trace_transaction(
        self, tx_hash: str, disable_memory=True, disable_storage=True
    ):
        """
        Function to trace a transaction
        """
        params = [
            tx_hash,
            {"disableMemory": disable_memory, "disableStorage": disable_storage},
        ]
        return self.web3.manager.request_blocking(
            "debug_traceTransaction", params=params
        )
