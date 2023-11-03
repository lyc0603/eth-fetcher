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
