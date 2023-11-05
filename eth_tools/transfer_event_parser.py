"""
Script to parse the transfer event from the blockchain
"""

import os
import json

from collections import defaultdict
from eth_tools.logger import logger


class TransferEventParser:
    """
    Parses ERC20 'transfer' events
    """

    def __init__(self, addresses: dict, start: int = None, end: int = None):
        self.addresses = addresses
        for key, val in self.addresses.items():
            self.addresses[key] = val

        # defaultdict is a dictionary that returns a default value if the key is not found
        self.balances = defaultdict(lambda: defaultdict(lambda: 0))
        self.last_update = defaultdict(lambda: 0)
        self.start = start
        self.end = end
        self.keys = {}
        self.keys["amount"] = "amount"
        self.keys["to"] = "to"
        self.keys["from"] = "from"

    def execute_events(self, events: list):
        """
        Method to iterate through the events and execute them
        """
        first_event = True
        for event in events:
            if event["event"] == "Transfer":
                if first_event:
                    self.set_keys(event)
                    self.start = (
                        self.start if self.start is not None else event["blockNumber"]
                    )
                    first_event = False
                self.handle_transfer_event(event)

    def handle_transfer_event(self, event: dict):
        """
        Method to handle the transfer event
        """
        if event["event"] != "Transfer":
            logger.warning("Failed to parse non-transfer event")
            return
        key_to = self.keys["to"]
        key_from = self.keys["from"]
        key_amount = self.keys["amount"]
        block = event["blockNumber"]
        if event["args"][key_from] in self.addresses.values():
            self.update_balance(
                event["args"][key_from], -1 * event["args"][key_amount], block
            )
        if event["args"][key_to] in self.addresses.values():
            self.update_balance(event["args"][key_to], event["args"][key_amount], block)

    def update_balance(self, account: str, change: int, block: int):
        """
        Method to update the balance of an account
        """
        last_updated_block = self.last_update[account]
        self.balances[account][block] = (
            self.balances[account][last_updated_block] + change
        )
        self.last_update[account] = block

    def find_key(self, event: dict, candidates: set):
        """
        Method to find the key in the event
        """

        # & is to find the intersection of two sets
        # next(iter()) is to get the first element of the set
        key = next(iter(candidates & event.keys()), None)
        if key:
            return key
        raise ValueError(f"none of {candidates} found in {event}")

    def set_keys(self, event: dict) -> bool:
        """
        ERC20 contracts don't follow a standard name for transfer args.
        This should be handled here.
        """
        self.keys["from"] = self.find_key(event["args"], {"from", "_from"})
        self.keys["to"] = self.find_key(event["args"], {"to", "_to"})
        self.keys["amount"] = self.find_key(
            event["args"], {"amount", "value", "_value"}
        )

    def write_balances(self, token: str, interval: int = None, filepath: str = None):
        """
        Method to write the balances to a file
        """
        for name, address in self.addresses.items():
            fname = token.lower() + "-balances:" + name.lower() + ".csv"
            if filepath is not None:
                fname = filepath + fname
            with open(fname, "w") as f:
                self.write_address_balances(address, f, interval)

    def write_address_balances(self, address, f, interval: int = None):
        """
        Method to write the balances of an address to a file
        """
        first_block = True
        last_balance = 0
        inter = 1 if interval is None else interval
        counter = 0
        for block in self.balances[address].keys():
            if first_block:
                last_block = block
                first_block = False
            if block == 0:
                continue
            # fill in missing blocks
            block_number = last_block + 1
            while block_number <= block - 1:
                counter += 1
                if counter % inter == 0:
                    self.log_balance(counter, f, block_number, last_balance)
                block_number += 1
            counter += 1
            if counter % inter == 0:
                self.log_balance(counter, f, block, self.balances[address][block])
            last_balance = self.balances[address][block]
            last_block = block

    def log_balance(self, counter: int, f, block_number: int, balance: int):
        """
        Method to log the balance
        """
        if self.start is not None and self.start > block_number:
            return
        if self.end is not None and self.end < block_number:
            return
        logger.info("Blocks: %i", counter)
        f.write(json.dumps({"blockNumber": block_number, "balance": balance}) + "\n")
