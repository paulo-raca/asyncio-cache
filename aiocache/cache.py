import asyncio
from .serializer import PickleSerializer
from .clock import SystemClock

class Cache():
    """
    Abstraction for an asynchronous cache
    """

    def __init__(self, clock=SystemClock()):
        self.clock = clock

    async def get(self, key):
        """
        Return cached value associated with key

        :Parameters:
            `key` : Key associated with the requested value
        :Exception:
            `KeyError`: If the value is not in the cache
        """
        raise NotImplemented()

    async def getOrDefault(self, key, default=None):
        try:
            return await self.get(key)
        except KeyError:
            return default

    async def put(self, key, value, ttl=None):
        """
        Adds a new value to the cache.

        Existing values associated with the key are replaced

        :Parameters:
            `key` : Key used to retrieve this value later
            `value` : Value stored in the cache
            `ttl` time before the value gets evicted, None to keep in the cache as long as possible
        """
        raise NotImplemented()

    async def remove(self, key):
        """
        Removes an existing value from the cache.

        No-op if the value isn't on the cache.

        :Parameters:
            `key` : Key associated with the evicted value
        """
        raise NotImplemented()

    async def remove_expired(self):
        """
        Cleanup expired entries from this dict
        """
        raise NotImplemented()


class NoCache(Cache):
    """
    An empty cache
    """

    async def get(self, key):
        raise KeyError(key)

    async def put(self, key, value, ttl=None):
        pass

    async def remove(self, key):
        pass

    async def remove_expired(self):
        pass

    async def data(self):
        return {}


class DictCache(Cache):
    """
    The simplest cache possible, stores data in a dict
    """

    def __init__(self, *args, **kwargs):
        Cache.__init__(self, *args, **kwargs)
        self._data = {}

    async def get(self, key):
        now = self.clock.now()
        value, expires_at = self._data[key]
        if expires_at is None or expires_at >= now:
            return value

    async def put(self, key, value, ttl=None):
        now = self.clock.now()
        expires_at = ttl + now if ttl is not None else None
        self._data[key] = (value, expires_at)

    async def remove(self, key):
        del self._data[key]

    async def remove_expired(self):
        now = self.clock.now()
        self._data = {
            key: (value, expires_at)
            for key, (value, expires_at) in self._data.items()
            if expires_at is None or expires_at >= now
        }

    async def data(self):
        now = self.clock.now()
        return {
            key: value
            for key, (value, expires_at) in self._data.items()
            if expires_at is None or expires_at >= now
        }


class SqliteCache(Cache):
    """
    A cache that uses sqlite as a storage backend
    """

    def __init__(self, filename=":memory:", serializer=PickleSerializer(), *args, **kwargs):
        Cache.__init__(self, *args, **kwargs)
        self.filename = filename
        self.serializer = serializer
        self.db = None
        self.db_lock = asyncio.Lock()

    async def get(self, key):
        async with self.db_lock:
            now = self.clock.now()
            await self._ensure_connected()
            async with self.db.execute('SELECT value, expires_at FROM cache WHERE key = ?', (key, )) as cursor:
                result = await cursor.fetchone()
                if result is not None:
                    value, expires_at = result
                    if expires_at is None or expires_at >= now:
                        return self.serializer.decode(value)
            raise KeyError(key)

    async def put(self, key, value, ttl=None):
        async with self.db_lock:
            now = self.clock.now()
            expires_at = ttl + now if ttl is not None else None
            await self._ensure_connected()
            await self.db.execute("""
                INSERT OR REPLACE INTO cache(key, value, expires_at)
                VALUES (?, ?, ?)
            """, (key, self.serializer.encode(value), expires_at, ))
            await self.db.commit()

    async def remove(self, key):
        async with self.db_lock:
            await self._ensure_connected()
            await self.db.execute("DELETE FROM cache WHERE key = ?", (key, ))
            await self.db.commit()

    async def remove_expired(self):
        async with self.db_lock:
            await self._remove_expired()

    async def data(self):
        now = self.clock.now()
        async with self.db_lock:
            await self._ensure_connected()
            async with self.db.execute('SELECT key, value, expires_at FROM cache') as cursor:
                return {
                    key: self.serializer.decode(value)
                    async for key, value, expires_at in cursor
                    if expires_at is None or expires_at >= now
                }

    async def _remove_expired(self):
        now = self.clock.now()
        await self._ensure_connected()
        await self.db.execute("DELETE FROM cache WHERE expires_at < ?", (now, ))

    async def _ensure_connected(self):
        if self.db is None:
            import aiosqlite
            self.db = await aiosqlite.connect(self.filename)
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key BLOB NOT NULL PRIMARY KEY,
                    value BLOB NOT NULL,
                    expires_at REAL
                );
            """)
            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS cache_expires_at_idx ON cache(expires_at);
            """)
            await self._remove_expired()
            await self.db.commit()

    async def _close(self) -> None:
        if self.db is not None:
            await self.db.close()
            self.db = None

    async def __aenter__(self):
        async with self.db_lock:
            await self._ensure_connected()
            return self

    async def __aexit__(self, exc_type, exc, tb):
        async with self.db_lock:
            await self._close()

    async def close(self):
        async with self.db_lock:
            await self._close()
