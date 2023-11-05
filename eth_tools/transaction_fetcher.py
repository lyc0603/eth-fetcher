"""
Script for fetching transactions from Etherscan
"""

import os

import requests

from eth_tools.logger import logger

ETHERSCAN_API_URL = "https://api.etherscan.io/api"
TRANSACTIONS_PER_PAGE = 1_000
MAX_TRANSACTIONS = 10_000


class TransactionsFetcher:
    """
    Retrieves transactions from Etherescan
    """

    def __init__(self, etherscan_api_key=None):
        if not etherscan_api_key:
            etherscan_api_key = os.environ.get("ETHERSCAN_API_KEY")
        if not etherscan_api_key:
            raise ValueError("ETHERSCAN_API_KEY not provided")
        self.etherscan_api_key = etherscan_api_key

        # Session is used to keep the connection alive
        self.session = requests.Session()

    def _make_transactions_request(self, address, page, internal=False):
        """
        Method to make a request to Etherscan for transactions
        """
        action = "txlistinternal" if internal else "txlist"
        response = self.session.get(
            ETHERSCAN_API_URL,
            params=dict(
                module="account",
                action=action,
                address=address,
                offset=TRANSACTIONS_PER_PAGE,
                page=page,
                sort="desc",
                apikey=self.etherscan_api_key,
            ),
        )
        if response.status_code != 200:
            raise ValueError(
                "failed to execute request: {0}".format(response.status_code)
            )
        return response.json()["result"]

    def fetch_contract_transactions(self, address, internal=False):
        """
        Method to fetch transactions for a contract
        """
        logger.debug("getting transactions (internal=%s) for %s", internal, address)
        count = 0
        for page in range(1, MAX_TRANSACTIONS // TRANSACTIONS_PER_PAGE + 1):
            logger.debug("requesting page %d for %s", page, address)
            returned_results = self._make_transactions_request(
                address, page, internal=internal
            )
            if not returned_results:
                break
            for transaction in returned_results:
                yield transaction
            count += len(returned_results)
        else:
            logger.warning(
                "more than %s transactions for %s, fetched first %s transactions",
                MAX_TRANSACTIONS,
                address,
                count,
            )
        logger.info(
            "fetched %s transactions (internal=%s) for %s", count, internal, address
        )
