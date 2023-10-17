"""
Script to fetch the abi of a contract from etherscan.io
"""

from typing import Iterable, List, Optional

import requests

from eth_tools.caching import cache

ABI_BASE_URL = "http://api.etherscan.io/api?module=contract&action=getabi&\
address={address}&format=raw"


@cache(ttl=-1, min_disk_time=0)
def fetch_abi(address: str, etherscan_api_key: Optional[str] = None) -> dict:
    """
    Function to fetch the abi of a contract from etherscan.io
    """
    url = ABI_BASE_URL.format(address=address)
    if etherscan_api_key:
        url += f"&apikey={etherscan_api_key}"
    return requests.get(url, timeout=120).json()


def fetch_abis(
    addressses: Iterable[str], etherscan_api_key: Optional[str] = None
) -> List[dict]:
    """
    Function to fetch the abis of a list of contracts from etherscan.io
    """
    return [fetch_abi(address, etherscan_api_key) for address in addressses]
