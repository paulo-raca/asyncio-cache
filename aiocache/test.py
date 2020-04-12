import aiounittest
import asyncio

class SerializerTest(aiounittest.AsyncTestCase):
    async def test_serializers(self):
        from .serializer import JsonSerializer, PickleSerializer
        for encoder in [JsonSerializer(), PickleSerializer()]:
            for data in ["foo", 12, [1,2,3], {"foo": "bar"}]:
                encoded = encoder.encode(data)
                decoded = encoder.decode(encoded)
                assert data == decoded
                print(f"{type(encoder)}: {data} -> {encoded} -> {decoded}")


class KeyMakerTest(aiounittest.AsyncTestCase):
    async def test_serializers(self):
        import hashlib
        from .key import ReprKeyMaker
        for key_maker in [ReprKeyMaker(), ReprKeyMaker(hash_args=hashlib.md5), ReprKeyMaker(hash=hashlib.sha256)]:
            print(key_maker(ReprKeyMaker.__init__, ["foo", "bar", "meh"], {"blah": 1, "bleh": {1, 2, 3}}))


class CacheTest(aiounittest.AsyncTestCase):
    async def test_caches(self):
        from .cache import NoCache, DictCache, SqliteCache
        from .clock import TestClock
        for cache in [NoCache(clock=TestClock()), DictCache(clock=TestClock()), SqliteCache(clock=TestClock())]:
            # Cache starts empty
            print(f"{type(cache)} -> {await cache.data()}")
            assert await cache.getOrDefault(b"foo") is None
            assert await cache.getOrDefault(b"baz") is None

            # Add one value
            await cache.put(b"foo", "bar")
            print(f"{type(cache)} -> {await cache.data()}")
            assert await cache.getOrDefault(b"foo") in ["bar", None]
            assert await cache.getOrDefault(b"baz") is None

            # Add another value
            await cache.put(b"baz", "xyz")
            print(f"{type(cache)} -> {await cache.data()}")
            assert await cache.getOrDefault(b"foo") in ["bar", None]
            assert await cache.getOrDefault(b"baz") in ["xyz", None]

            # Invalidate one value
            await cache.remove(b"foo")
            print(f"{type(cache)} -> {await cache.data()}")
            assert await cache.getOrDefault(b"foo") is None
            assert await cache.getOrDefault(b"baz") in ["xyz", None]

            # Insert with TTL
            await cache.put(b"ttl", {1, 2, 3}, ttl=1)
            print(f"{type(cache)} -> {await cache.data()}")
            assert await cache.getOrDefault(b"ttl") in [{1, 2, 3}, None]
            assert await cache.getOrDefault(b"foo") is None
            assert await cache.getOrDefault(b"baz") in ["xyz", None]

            # Wait for invalidation
            await cache.clock.sleep(2)
            print(f"{type(cache)} -> {await cache.data()}")
            assert await cache.getOrDefault(b"ttl") is None
            assert await cache.getOrDefault(b"foo") is None
            assert await cache.getOrDefault(b"baz") in ["xyz", None]

            if isinstance(cache, SqliteCache):
                await cache.close()

class DecoratorTest(aiounittest.AsyncTestCase):
    async def test_decorator(self):
        from .decorator import cached
        from datetime import timedelta
        @cached(ttl=(1,timedelta(minutes=1)))
        async def cached_func(ret, *args):
            return ret

        print(f"cached_func.cache={await cached_func.cache.data()}")
        a1 = await cached_func({}, "a")
        print(f"cached_func.cache={await cached_func.cache.data()}")
        a2 = await cached_func({}, "a")
        print(f"cached_func.cache={await cached_func.cache.data()}")
        b1 = await cached_func({}, "b")
        print(f"cached_func.cache={await cached_func.cache.data()}")
        b2 = await cached_func({}, "b")
        print(f"cached_func.cache={await cached_func.cache.data()}")
        assert a1 is a2
        assert b1 is b2
        assert a1 == b1
        assert a1 is not b1

        await cached_func.invalidate({}, "a")
        print(f"cached_func.cache={await cached_func.cache.data()}")
        a3 = await cached_func({}, "a")
        print(f"cached_func.cache={await cached_func.cache.data()}")
        assert a1 == a3
        assert a1 is not a3

        for i in range(100):
            await cached_func(i)


