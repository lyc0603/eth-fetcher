"""
CLI for eth_tools
"""

import os
from argparse import ArgumentParser

from eth_tools import commands
from eth_tools import constants
from eth_tools.contract_caller import DEFAULT_BLOCK_INTERVAL


def environ_or_required(key):
    """
    Function to return a dictionary with a default value if the given key is
    """
    default_value = os.environ.get(key)
    if default_value:
        return {"default": default_value}
    return {"required": True}


def add_web3_uri(subparser):
    """
    Function to add a --web3-uri command line argument to the given subparser
    """
    subparser.add_argument(
        "--web3-uri", help="URI of Web3", **environ_or_required("WEB3_PROVIDER_URI")
    )


def add_etherscan_api_key(subparser):
    """
    Function used to add an --etherscan-api-key command line argument to the
    """
    subparser.add_argument(
        "--etherscan-api-key",
        help="API key for Etherscan",
        **environ_or_required("ETHERSCAN_API_KEY"),
    )


# prog is the name of the program
parser = ArgumentParser(prog="ethereum-tools")

# dest is the name of the attribute to hold the value
subparsers = parser.add_subparsers(dest="command", help="Command to execute")


# FETCH BLOCKS
# create a subparser for the command "fetch-blocks"
fetch_block_timestamps_parser = subparsers.add_parser(
    "fetch-blocks", help="fetches information about given blocks"
)

add_web3_uri(fetch_block_timestamps_parser)
fetch_block_timestamps_parser.add_argument(
    # -f is the short name, --fields is the long name
    "-f",
    "--fields",
    # nargs="+" means one or more arguments
    nargs="+",
    # default is the default value if the argument is not given
    default=constants.DEFAULT_BLOCK_FIELDS,
    help="fields to fetch from the block",
)

# add a mutually exclusive group for the arguments --from and --to
fetch_blocks_group = fetch_block_timestamps_parser.add_mutually_exclusive_group()
fetch_blocks_group.add_argument(
    "--block",
    help="Path to a file containing a list of blocks to fetch (1 block number per line)",
)

fetch_blocks_group_range = fetch_blocks_group.add_argument_group()
fetch_blocks_group_range.add_argument(
    "-s",
    "--start-block",
    type=int,
    help="block from which to fetch timestamps",
)
fetch_blocks_group_range.add_argument(
    "-e", "--end-block", type=int, help="block up to which to fetch timestamps"
)
fetch_block_timestamps_parser.add_argument(
    "-o", "--output", required=True, help="output file"
)
fetch_block_timestamps_parser.add_argument(
    "--log-interval", type=int, default=1_000, help="interval at which to log"
)


# FETCH TRANSCATION
fetch_address_transactions_parser = subparsers.add_parser(
    "fetch-address-transactions",
    help="fetches information about the transactions of a given address from Etherscan",
)
add_etherscan_api_key(fetch_address_transactions_parser)
fetch_address_transactions_parser.add_argument(
    "-a", "--address", required=True, help="address for which to get transactions"
)
fetch_address_transactions_parser.add_argument(
    "--internal",
    default=False,
    action="store_true",
    help="fetch information about internal transactions rather than regular ones",
)
fetch_address_transactions_parser.add_argument(
    "-o", "--output", required=True, help="output file"
)

fetch_transactions_parser = subparsers.add_parser(
    "fetch-transactions",
    help="fetches transactions in given files from an Ethereum node",
)
add_web3_uri(fetch_transactions_parser)
fetch_transactions_parser.add_argument(
    "files", nargs="+", help="files containing transactions to trace"
)
fetch_transactions_parser.add_argument(
    "-r",
    "--include-receipt",
    action="store_true",
    default=False,
    help="include transaction receipt",
)
fetch_transactions_parser.add_argument(
    "-t",
    "--include-traces",
    action="store_true",
    default=False,
    help="include transaction traces",
)
fetch_transactions_parser.add_argument(
    "-o", "--output", required=True, help="output file"
)

# CALL CONTRACT
call_contract_parser = subparsers.add_parser(
    "call-contract", help="call contract regularly between blocks"
)
add_web3_uri(call_contract_parser)
call_contract_parser.add_argument("address", help="address of the contract")
call_contract_parser.add_argument("--abi", help="path to the contract abi")
call_contract_parser.add_argument("-s", "--start", type=int, help="start block")
call_contract_parser.add_argument("-e", "--end", type=int, help="end block")
call_contract_parser.add_argument(
    "-i",
    "--interval",
    type=int,
    default=DEFAULT_BLOCK_INTERVAL,
    help="interval between calls",
)
call_contract_parser.add_argument(
    "-f", "--func", required=True, help="function to call"
)
call_contract_parser.add_argument(
    "--args", nargs="*", help="arguments to pass to the function"
)
call_contract_parser.add_argument("-o", "--output", help="output file")

# FETCH EVENTS
fetch_events_parser = subparsers.add_parser(
    "fetch-events", help="Fetches the events from the given contract"
)
add_web3_uri(fetch_events_parser)
fetch_events_parser.add_argument("address", help="Address of the contract")
fetch_events_parser.add_argument("--abi", help="Path to the contract ABI")
fetch_events_parser.add_argument(
    "-s",
    "--start-block",
    help="Start block to fetch the events",
    required=True,
    type=int,
)
fetch_events_parser.add_argument(
    "-e", "--end-block", help="End block to fetch the events", type=int
)
fetch_events_parser.add_argument(
    "-o",
    "--output",
    required=True,
    help="Output jsonl file to store the results (.gz recommended)",
)

# BULK FETCH EVENTS
bulk_fetch_events_parser = subparsers.add_parser(
    "bulk-fetch-events", help="Fetches the events from the given contracts"
)
add_web3_uri(bulk_fetch_events_parser)
bulk_fetch_events_parser.add_argument(
    "-c", "--config", help="Config file to fetch events"
)
bulk_fetch_events_parser.add_argument("--abis", help="Directory containing ABIs")
bulk_fetch_events_parser.add_argument(
    "-o",
    "--output",
    required=True,
    help="Output directory to store the results",
)

# GET BALANCES EVENTS

get_balances_event_parser = subparsers.add_parser(
    "get-balances",
    help="parses 'transfer' events to compute balances of given addresses",
)
get_balances_event_parser.add_argument(
    "-a",
    "--addresses",
    required=True,
    help="json file containing addresses to get balances for",
)
get_balances_event_parser.add_argument(
    "-t", "--token", required=True, help="token symbol (used for output file name)"
)
get_balances_event_parser.add_argument(
    "-d", "--events", required=True, help="file containing events to parse"
)
get_balances_event_parser.add_argument(
    "-s",
    "--start-block",
    type=int,
    help="block from which to fetch timestamps",
)
get_balances_event_parser.add_argument(
    "-e", "--end-block", type=int, help="block up to which to compute balances"
)
get_balances_event_parser.add_argument(
    "-o", "--output", required=True, help="output file path"
)
get_balances_event_parser.add_argument(
    "--log-interval", type=int, default=1_000, help="interval at which to log"
)

# FETCH ABIS
fetch_abis_parser = subparsers.add_parser(
    "fetch-abis",
    help="fetches ABI information of contracts from Etherscan",
)
add_etherscan_api_key(fetch_abis_parser)
fetch_abis_parser.add_argument("input", help="file containing the contracts to fetch")
fetch_abis_parser.add_argument("-o", "--output", required=True, help="output directory")


def run():
    """
    Function to run the CLI
    """
    # parse the arguments
    args = vars(parser.parse_args())

    # if no command is given, print help
    if not args["command"]:
        parser.error("no command given")

    # get the function to run
    func = getattr(commands, args["command"].replace("-", "_"))
    func(args)
