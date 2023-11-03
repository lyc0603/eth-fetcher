"""
Class for fetching events from the blockchain
"""

from argparse import RawTextHelpFormatter
import json
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from os import path
from typing import Iterable, Iterator, List, Optional

from eth_typing import Address
from web3 import Web3
from web3.contract import Contract
from web3.types import FilterParams, LogReceipt

from eth_tools.json_encoder import EthJSONEncoder
from eth_tools.logger import logger
from eth_tools.utils import smart_open


# @dataclass(repr=False): 这是一个装饰器，用于装饰类定义。在这里，@dataclass用于创建
# 一个数据类（data class）。repr=False参数指定不要为该类生成默认的__repr__方法，这意
# 味着不会自动创建一个用于生成类实例的字符串表示的方法。开发者选择手动定义__repr__方法，
# 如代码中后面所示。
@dataclass(repr=False)

# 总之，@dataclass(repr=False)装饰器用于创建一个轻量级的数据类，其中包含了一些属性，这些
# 属性的类型和默认值都被定义，以便更轻松地创建和管理这些属性。而且，开发者可以选择手动定义
# __repr__方法，以提供自定义的类实例表示形式。


class FetchTask:
    """
    class to represent a task for fetching events
    """

    address: str
    abi: dict
    start_block: int
    end_block: Optional[int] = None
    name: Optional[str] = None

    @property
    def checksum_address(self) -> Address:
        """
        checksum_address 是一个属性方法,用于返回给定地址的checksum格式地址。通过使用
        @property 装饰器，它可以像属性一样访问，而不需要使用括号进行调用。
        """
        return Web3.toChecksumAddress(self.address)

    # 这个 __repr__ 方法用于返回一个字符串，该字符串包含了 FetchTask 类实例的属性值，
    # 以提供有关对象的信息。在使用 print 函数或者在交互式环境中查看对象时，会自动调用
    # __repr__ 方法以显示对象的字符串表示形式。这有助于开发者更好地理解对象的内容和状态。
    def __repr__(self) -> str:
        return (
            f"FetchTask(address='{self.address}', "
            f"start_block={self.start_block}, end_block={self.end_block})"
        )

    @property
    def display_name(self):
        """
        Method to return a display name for the task
        """
        if self.name:
            return self.name
        return self.address

    @classmethod
    def from_dict(cls, raw_task: dict, abi_paths: str = None):
        """
        from_dict 方法的目的是从一个字典中创建一个 FetchTask 类的实例，并为该实例设置
        相应的属性值。在这个过程中，它处理了默认值、文件路径等情况，以确保创建正确的类实例。
        """
        # 这一行创建了 raw_task 的一个副本，以确保在修改 raw_task 时不会影响原始的输入字典。
        raw_task = raw_task.copy()
        # 这一行定义了一个变量 default_abi_name，它用于获取字典中的 "name" 键的值，如果该
        # 键不存在，则使用 "address" 键的值。然后， .lower() 方法将名称转换为小写字母。
        default_abi_name = raw_task.get("name", raw_task["address"]).lower()

        # 这一行定义了一个变量 abi_path，它用于获取字典中的 "abi" 键的值，如果该键不存在，
        # 则使用 default_abi_name + ".json" 作为默认值。这一行还使用 pop 方法从
        # raw_task 中删除 "abi" 键，以避免后续重复使用。
        abi_path = raw_task.pop("abi", default_abi_name + ".json")
        if abi_paths:
            abi_path = path.join(abi_paths, abi_path)
        with smart_open(abi_path) as f:
            raw_task["abi"] = json.load(f)
        keys = ["address", "abi", "start_block", "end_block", "name"]
        # 最后，这一行使用字典解构（dictionary unpacking）将从 raw_task 中提取的属性值
        # 传递给类的构造函数（cls），以创建一个新的类实例对象。这个方法允许从字典中创建一个
        # FetchTask 类的实例，其中包含了从 raw_task 中提取的属性。
        return cls(**{k: raw_task.get(k) for k in keys})


class ContractFetcher:
    """
    用于封装与合约事件数据提取相关的功能。
    """

    # 这一行定义了一个类级别的属性 BLOCK_GRANULARITIES，它是一个包含整数的列表，
    # 用于表示提取事件数据时的块粒度（granularity）。这个属性被所有类实例共享。
    BLOCK_GRANUALARITIES = [10_000, 1_000, 100, 10, 1]

    def __init__(self, contract: Contract):
        self.contract = contract
        contract_events = [event() for event in self.contract.events]  # type: ignore
        self.events_by_topic = {
            event.build_filter().topics[0]: event
            for event in contract_events
            if not event.abi["anonymous"]
        }

    def process_log(self, event: LogReceipt) -> LogReceipt:
        """
        Function to process a log receipt
        """
        topics = event.get("topics")
        if topics and topics[0].hex() in self.events_by_topic:
            event = self.events_by_topic[topics[0].hex()].processLog(event)
        return event

    def process_logs(self, events: List[LogReceipt]) -> List[LogReceipt]:
        """
        Function to process a list of log receipts
        """
        return [self.process_log(event) for event in events]

    def _fetch_events(self, start_block: int, end_block: int) -> Iterable[LogReceipt]:
        event_filter = self.contract.web3.eth.filter(
            FilterParams(
                address=self.contract.address, fromBlock=start_block, toBlock=end_block
            )
        )
        events = event_filter.get_all_entries()
        return self.process_logs(events)

    def _fetch_batch_parallel(
        self, start_blocks: List[int], end_blocks: List[int]
    ) -> Iterable[LogReceipt]:
        if len(start_blocks) == 1:
            return self._fetch_events(start_blocks[0], end_blocks[0])
        result = []
        with ThreadPoolExecutor(max_workers=20) as executor:
            for events in executor.map(self._fetch_events, start_blocks, end_blocks):
                result.extend(events)
        return result

    def _fetch_batch(self, start_block: int, end_block: int) -> Iterable[LogReceipt]:
        for granularity in self.BLOCK_GRANULARITIES:
            block_count = end_block - start_block + 1
            iterations = range(math.ceil(block_count / granularity))
            start_blocks = [(start_block + i * granularity) for i in iterations]
            end_blocks = [min(b + granularity - 1, end_block) for b in start_blocks]
            try:
                return self._fetch_batch_parallel(start_blocks, end_blocks)
            except Exception:  # pylint: disable=broad-except
                pass
        raise ValueError(
            f"unable to fetch events for {self.contract.address} "
            f"from block {start_block} to {end_block}"
        )

    def fetch_events(
        self, start_block: int, end_block: int = None
    ) -> Iterator[LogReceipt]:
        if end_block is None:
            end_block = self.contract.web3.eth.blockNumber

        block_count = end_block - start_block + 1
        granularity = self.BLOCK_GRANULARITIES[0]

        for i in range(math.ceil(block_count / granularity)):
            logger.info(
                "%s progress: %s/%s",
                self.contract.address,
                i * granularity,
                block_count,
            )
            batch_start_block = start_block + i * granularity
            batch_end_block = min(batch_start_block + granularity - 1, end_block)
            yield from self._fetch_batch(batch_start_block, batch_end_block)


class EventFetcher:
    def __init__(self, web3: Web3):
        self.web3 = web3

    def fetch_events(self, task: FetchTask) -> Iterator[LogReceipt]:
        contract = self.web3.eth.contract(address=task.checksum_address, abi=task.abi)
        fetcher = ContractFetcher(contract)
        return fetcher.fetch_events(task.start_block, task.end_block)

    def fetch_and_persist_events(self, task: FetchTask, output_file: str):
        with smart_open(output_file, "w") as f:
            for event in self.fetch_events(task):
                print(json.dumps(event, cls=EthJSONEncoder), file=f)

    def fetch_all_events(self, fetch_tasks: List[FetchTask], output_directory: str):
        with ThreadPoolExecutor() as executor:
            filepaths = [
                path.join(output_directory, task.display_name) + ".jsonl.gz"
                for task in fetch_tasks
            ]
            futures = {
                executor.submit(self.fetch_and_persist_events, task, output): task
                for task, output in zip(fetch_tasks, filepaths)
            }
            for future in as_completed(futures):
                task = futures[future]
                ex = future.exception()
                if ex:
                    logger.error(
                        "failed to process %s (%s): %s", task.name, task.address, ex
                    )
                else:
                    logger.info("completed to process %s (%s)", task.name, task.address)
