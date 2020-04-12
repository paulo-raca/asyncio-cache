import random
import asyncio
from functools import wraps
from .cache import DictCache
from .key import ReprKeyMaker
from datetime import timedelta

def _parse_timedelta(t):
    if t is None:
        return None
    elif isinstance(t, (int, float)):
        return t
    elif isinstance(t, timedelta):
        return t.total_seconds()
    else:
        raise ValueError(f"Timedelta must be a None, Number or datetime.timedelta, got {repr(t)}")

def _parse_ttl_function(ttl):
    # TTL is None: turn off caching
    if ttl is None:
        return lambda fn, args, kwargs, value: None
    # TTL is a constant value
    elif isinstance(ttl, (int, float, timedelta)):
        ttl_value = _parse_timedelta(ttl)
        return lambda fn, args, kwargs, value: ttl_value
    # TTL is a tuple (ttl_min, ttl_max)
    elif isinstance(ttl, tuple) and len(ttl) == 2:
        ttl_min = _parse_timedelta(ttl[0])
        ttl_max = _parse_timedelta(ttl[1])
        if ttl_min is None or ttl_max is None:
            raise ValueError(f"TTL range cannot be None: {repr((ttl_min, ttl_max))}")
        return lambda fn, args, kwargs, value: random.uniform(ttl_min, ttl_max)
    elif isinstance(ttl, tuple) and len(ttl) == 2:
        return lambda fn, args, kwargs, value: _parse_timedelta(ttl(fn, args, kwargs, value))
    else:
        raise ValueError("TTL must be a None, constant, tuple(constant_min, constant_max), or function(fn, args, kwargs, value)")

def cached(cache=DictCache(), key_maker=ReprKeyMaker(), ttl=None):
    ttl = _parse_ttl_function(ttl)
    ongoing = {}
    ongoing_lock = asyncio.Lock()


    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            key = key_maker(fn, args, kwargs)

            async def get_or_compute():
                try:
                    return await cache.get(key)
                except KeyError:
                    pass

                value = await fn(*args, **kwargs)
                value_ttl = ttl(fn, args, kwargs, value)
                await cache.put(key, value, value_ttl)
                return value

            async with ongoing_lock:
                pending = ongoing.get(key, None)
                if pending is None:
                    pending = asyncio.create_task(get_or_compute())
                    ongoing[key] = pending
                    pending.add_done_callback(lambda x: ongoing.pop(key))

            return await pending


        async def invalidate(*args, **kwargs):
            key = key_maker(fn, args, kwargs)
            await cache.remove(key)

        wrapper.fn = fn
        wrapper.cache = cache
        wrapper.key_maker = key_maker
        wrapper.ttl = ttl
        wrapper.invalidate = invalidate
        return wrapper
    return decorator
