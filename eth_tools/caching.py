"""
Decorator factory to implement caching of data
"""
import functools
import hashlib
import os
import pickle
import time
from os import path

CACHE_PATH = path.join(os.environ["HOME"], ".cache", "eth_tools")


def cache(
    ttl: int,
    min_memory_time: float = 0.1,
    min_disk_time: float = 2.0,
    directory: str = CACHE_PATH,
    exclude: dict = None,
    should_cache=None,
):
    """
    Decorator using on-disk cacheing. If the function call takes more than
    ``min_memory_time`` and less than ``min_disk_time``, the reults will be
    cached in memory. If the call takes more than ``min_disk_time``, the result
    will be cached inside ``directory`` as a pickle file.
    Regardless of the storage, cached results are used only ofr ``ttl`` seconds.
    If the ``ttl`` us set to a negative value, the cache will never be expired.
    The function results is cached based on its name and the arguments it has
    been pased. This means that if the function is not passed the exact
    same arguments, the result will not be re-used.
    """
    os.makedirs(CACHE_PATH, 0o755, exist_ok=True)

    if exclude is None:
        exclude = {}

    def compute_key(func_name, args, kwargs):
        """
        Computes a key to be used for the function result
        depending on the function name and its arguments
        """

        reconstructed_args = []
        for i, arg in enumerate(args):
            # If the argument is not excluded, add it to the list
            if i not in exclude.get("args", []):
                reconstructed_args.append(arg)
        for arg in exclude.get("kwargs", []):
            # Remove the key from the kwargs
            del kwargs[arg]

        # pickle the arguments
        to_hash = pickle.dumps((func_name, reconstructed_args, kwargs))

        # create a md5 hash object
        md5sum = hashlib.md5()

        # update the Bytes to be hashed
        md5sum.update(to_hash)

        # return the hex string
        return md5sum.hexdigest()

    def should_use_file_cache(filepath):
        """
        Return ``True``if the file cache should be used.
        """

        try:
            stats = os.stat(filepath)
            if 0 <= ttl <= int(time.time() - stats.st_mtime):
                # If the file is older than the ttl, delete it
                os.unlink(filepath)
                return False
            return True
        except FileNotFoundError:
            return False

    def decorator(fn):
        """
        decorator function
        """

        memory_cache = {}

        def get_from_memory_cache(key):
            """
            Return two values, the second indicates if the value was cached
            or not. If the second value is true, the first value is the
            actual cached value.
            """

            # get the value from the memory cache
            entry = memory_cache.get(key)
            if not entry:
                return None, False
            iserted_at, value = entry
            if 0 <= ttl <= int(time.time() - iserted_at):
                # If the value is older than the ttl, delete it
                del memory_cache[key]
                return None, False
            return value, True

        # *wrap the arg into tuple args
        # **wrap the kwargs into dict kwargs
        def decorated(*arg, **kwargs):
            """
            decorated function
            """
            # compute unique on the function name and arguments
            key = compute_key(fn.__name__, arg, kwargs)

            # return from memory if possible
            value, cached = get_from_memory_cache(key)
            if value is not None and cached:
                return value

            # return from disk if possible
            filename = f"{key}.pkl"
            filepath = path.join(directory, filename)
            if should_use_file_cache(filepath):
                with open(filepath, "rb") as f:
                    return pickle.load(f)

            # not cached, call the function
            start = time.time()
            result = fn(*arg, **kwargs)
            ellapse = time.time() - start

            # if should_cached function is provided
            if should_cache is not None and not should_cache(result, *arg, **kwargs):
                return result

            # if ellapsed time is long enough to store in memory
            # short enough not to fall back to dis storage or disk storage is disabled
            # add to memory cache
            if min_memory_time <= ellapse < min_disk_time:
                memory_cache[key] = (time.time(), result)

            # if ellapsed time is long, use disk storage
            elif ellapse >= min_disk_time:
                with open(filepath, "wb") as f:
                    pickle.dump(result, f)
            return result

        return functools.wraps(fn)(decorated)

    return decorator
