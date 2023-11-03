"""
Contract caller
"""

import multiprocessing
from concurrent.futures import ThreadPoolExecutor

from retry import retry
from web3 import Web3
from web3.contract import Contract

from eth_tools.logger import logger

DEFAULT_BLOCK_INTERVAL = 1_000


ARG_TYPES = {
    "u256": int,
    "address": Web3.toChecksumAddress,
}


class ContractCaller:
    def __init__(self, contract: Contract):
        self.contract = contract

    def collect_results(
        self,
        func_name,
        start_block,
        end_block=None,
        block_interval=DEFAULT_BLOCK_INTERVAL,
        contract_args=None,
    ):
        max_workers = multiprocessing.cpu_count() * 5
        if end_block is None:
            end_block = self.contract.web3.eth.blockNumber
        if start_block is None:
            start_block = end_block
        if contract_args is None:
            contract_args = []
        contract_args = [self.transform_arg(arg) for arg in contract_args]

        def run_task(block):
            try:
                return self.call_func(func_name, block, contract_args)
            except Exception as ex:  # pylint: disable=broad-except
                logger.error("failed to fetch block %s: %s", block, ex)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            blocks = range(start_block, end_block + 1, block_interval)
            total_count = len(blocks)
            results = executor.map(run_task, blocks)
            for i, (block, result) in enumerate(zip(blocks, results)):
                if i % 10 == 0 and total_count > 10:
                    logger.info(
                        "progress: %s/%s (%.2f%%)",
                        i,
                        total_count,
                        i / total_count * 100,
                    )
                if result is not None:
                    yield (block, result)

    @retry(delay=1, backoff=2, tries=3, logger=logger)
    def call_func(self, func_name, block, contract_args):
        func = getattr(self.contract.functions, func_name)
        return func(*contract_args).call(block_identifier=block)

    def transform_arg(self, raw_arg: str):
        if not isinstance(raw_arg, str):
            return raw_arg
        args = raw_arg.split(":")
        if len(args) == 1:
            return args[0]
        arg, arg_type = args
        cast = ARG_TYPES.get(arg_type)
        if not cast:
            raise ValueError(f"unknown type {arg_type}")
        return cast(arg)
