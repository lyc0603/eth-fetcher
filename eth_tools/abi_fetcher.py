"""
Functions for fetching ABIs from Etherscan.
"""

from typing import Iterable, List, Optional

import requests

from eth_tools.caching import cache

ABI_BASE_URL = "http://api.etherscan.io/api?module=contract&action=getabi&address={address}&format=raw"


@cache(ttl=-1, min_disk_time=0)
def fetch_abi(address: str, etherscan_api_key: Optional[str] = None) -> dict:
    url = ABI_BASE_URL.format(address=address)
    if etherscan_api_key:
        url += f"&apikey={etherscan_api_key}"
    return requests.get(url).json()


def fetch_abis(
    addresses: Iterable[str], etherscan_api_key: Optional[str] = None
) -> List[dict]:
    return [
        fetch_abi(address, etherscan_api_key=etherscan_api_key) for address in addresses
    ]
