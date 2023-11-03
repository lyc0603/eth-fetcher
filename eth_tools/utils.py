"""
Function to create a IO[str] object from a URI.
"""

from typing import IO, cast

# smart_open is a uniform file-like object opener for Python
from smart_open import open as _smart_open


def smart_open(
    # URL and URN are both valid URI
    uri,
    mode="r",
    buffering=-1,
    encoding=None,
    errors=None,
    newline=None,
    closefd=True,
    opener=None,
    transport_params=None,
) -> IO[str]:
    """Returns a IO for the given URI"""
    return cast(
        # IO stream is the method to read and write data
        IO,
        _smart_open(
            uri,
            mode=mode,
            buffering=buffering,
            encoding=encoding,
            errors=errors,
            newline=newline,
            closefd=closefd,
            opener=opener,
            transport_params=transport_params,
        ),
    )
