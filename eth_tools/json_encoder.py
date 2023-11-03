"""
Ethereum JSON encoder
"""

from json import JSONEncoder

from web3.datastructures import AttributeDict
from web3.types import HexBytes


class EthJSONEncoder(JSONEncoder):
    """custom JSON encoder for web3 types"""

    def default(self, o):
        if isinstance(o, HexBytes):
            return o.hex()
        if isinstance(o, AttributeDict):
            return dict(o)
        if isinstance(o, bytes):
            return o.hex()
        # use the default encoder as fallback
        return super().default(o)
