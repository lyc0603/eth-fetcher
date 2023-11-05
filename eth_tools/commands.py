"""
Commands for eth_tools
"""

import csv
import json
import sys
from contextlib import contextmanager
from functools import wraps
from os import path
from typing import IO, Iterator

from eth_typing import Address
from web3 import Web3
from web3.providers.auto import load_provider_from_uri

from eth_tools import abi_fetcher, constants
from eth_tools.block_iterator import BlockIterator
from eth_tools.contract_caller import ContractCaller
from eth_tools.event_fetcher import EventFetcher, FetchTask
from eth_tools.json_encoder import EthJSONEncoder
from eth_tools.logger import logger
from eth_tools.transaction_fetcher import TransactionsFetcher
from eth_tools.transaction_tracer import TransactionTracer
from eth_tools.transfer_event_parser import TransferEventParser
from eth_tools.utils import smart_open


def uses_web3(f):
    """
    Decorator for functions that use a Web3 instance.
    """

    @wraps(f)
    def wrapper(args):
        web3 = create_web3(args["web3_uri"])
        return f(args, web3)

    return wrapper


def uses_etherscan(f):
    """
    Decorator for functions that use an Etherscan API key.
    """

    @wraps(f)
    def wrapper(args):
        etherscan_key = args["etherscan_api_key"]
        return f(args, etherscan_key)

    return wrapper


def create_web3(uri: str):
    """
    Function to create a Web3 instance from a URI.
    """

    provider = load_provider_from_uri(uri, {"timeout": 60})
    return Web3(provider=provider)


@uses_web3
def fetch_blocks(args: dict, web3: Web3):
    """
    Fetches blocks and stores them in the file given in arguments
    """

    blocks = None
    if args["blocks"]:
        with open(args["blocks"]) as f:
            # map is a function to apply a function to each element of an iterable
            blocks = list(map(int, f))
    block_iterator = BlockIterator(
        web3,
        start_block=args["start_block"],
        end_block=args["end_block"],
        blocks=blocks,
        log_interval=args["log_interval"],
    )
    fields = args["fields"]

    # with is a context manager to automatically close the file
    with smart_open(args["output"], "w") as f:
        # DictWriter is a class to write dict rows easily
        writer = csv.DictWriter(f, fieldnames=fields)

        # writeheader writes the header of the CSV file
        writer.writeheader()
        for block in block_iterator:
            # getattr is a function to get an attribute from an object
            row = {field: getattr(block, field) for field in fields}
            writer.writerow(row)


def get_balances(args: dict):
    """
    Parses 'transfer' events of an ERC20 contract to compute balances
    """
    with open(args["addresses"]) as f:
        addresses = json.load(f)
    start = args.get("start_block")
    end = args.get("end_block")
    event_parser = TransferEventParser(addresses, start=start, end=end)
    with open(args["events"]) as f:
        events = [json.loads(e) for e in f]
    event_parser.execute_events(events)
    event_parser.write_balances(
        args["token"], interval=args["log_interval"], filepath=args["output"]
    )


@uses_etherscan
def fetch_address_transactions(args: dict, etherscan_key: str):
    """
    Function to fetch transactions from an address
    """
    fetcher = TransactionsFetcher(etherscan_api_key=etherscan_key)
    internal = args["internal"]
    if internal:
        fields = constants.ETHERSCAN_INTERNAL_TRANSACTION_KEYS
    else:
        fields = constants.ETHERSCAN_TRANSACTION_KEYS
    with smart_open(args["output"], "w") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for transaction in fetcher.fetch_contract_transactions(
            args["address"], internal=internal
        ):
            writer.writerow(transaction)
