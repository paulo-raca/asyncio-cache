# Asyncio Caches

This library aims to make caching simple in asyncio code.

## Decorator

The easiest way of using this library is with the `@cached` decorator:

```
@cached()
async def cached_func(*args, **kwargs):
    return await doSomething()
```

This will automatically store and reuse results from this function.

Of course, you can tweak it to your needs

### TTL

There are many ways to specify how long each value should stay in the cache:

- `None` (**default**): The data doesn't expire.

    ```python
    @cached(ttl=None)
    async def never_expires():
        return await doSomething()
    ```

- `time`: The data always expires after the specified amount of time.

    ```python
    @cached(ttl=60)  # or @cached(ttl=timedelta(minutes=1))
    async def expires_after_1_minute():
        return await doSomething()
    ```

- `(min, max)`: The actual ttl is different for each value, and is a random value in the [min, max] interval. Useful to avoid invalidating all data at the same time.

    ```python
    @cached(ttl=(timedelta(minutes=30), timedelta(minutes=60)))
    async def expires_between_30_and_60_minutes():
        return await doSomething()
    ```

- `function(fn, args, kwargs, value)`: An user-defined function to define the TTL based on the function, its arguments, and the result

### Cache

The cache implementation is the most important parameter in a cached function call.

You can specify the cache instance using the `cache=` argument:

```python
@cached(cache=SqliteCache('cache.db'))
async def cached_func(arg):
    return await doSomething()
```

The default cache is an in-memory `DictCache`

### KeyMaker

The KeyMaker computes a cache key from a function call.

You can specify how to get the key from a call using the `key_maker=` argument. e.g.:

```python
@cached(key_maker=lambda fn, args, kwargs: f"{args[0]}_{args[1]}".encode('utf-8'))
async def cached_func(arg0, arg1):
    return await doSomething()
```

The default key maker is an `ReprKeyMaker` and should be fine for most cases

## Types

### Cache

Caches are the main data structure in this library.

They do all the things you would expect: Add data, fetch it back, invalidate it. Automatically is also supported.

#### API

- `async def get(key)`: Return cached value associated with key, or raises ValueError
- `async def getOrDefault(key, default=None)`: Return cached value associated with key, or the default value
- `async def put(key, value, ttl=None)`: Stores a value on the cache. If specified, the value gets removed automatically after `ttl` seconds have elapsed
- `async def remove(key)`: Manually invalidates an entry in the cache, if any
- `async def remove_expired()`: Manually triggers the eviction of expired data

#### Implementations

- `DictCache` (**default**): An in-memory cache that stores data in an internal `dict`
- `SqliteCache`: An in-disk cache that stores data in an SQLite database
- `NoCache`: This is a cache that doesn't actually remember anything. Sometimes useful for testing
- `Other`: You can easily implement your own by extending aiocache.Cache

### KeyMaker

This helper function translates a function and its arguments into a cache key.

This is necessary to extract the cache key from a function call when using the `@cached()` decorator

#### API

- `def __call__(fn, args, kwargs)`: Returns a blob that can identify the function and its parameters

#### Implementations

- `ReprKeyMaker` (**default**): This assembles a key with the function name and the `repr` of all its arguments. Optionally, it hashes the result to get a smaller cache key.
- `Other`: You can easily implement your own by extending aiocache.KeyMaker


### Serializers

Serializers are used to transform a value into a binary blob and to load it back.

This is a necessary step for any cache that doesn't live in the program memory. You may specify a serializer when instantiating a compatible cache. e.g., `SqliteCache(serializer=PickleSerializer())`

#### API

- `def encode(value)`: Encodes `value` as a binary blob (`bytes`)
- `def decode(encoded)` Decodes binary blob (`bytes`) back into an usable value

#### Implementations

- `PickleSerializer` (**default**): This is based on Python's `pickle` module, and should work with most Python data structures
- `JsonSerializer`: This serializes the data in `JSON`, which is convenient for caching simple data structures and responses from REST APIs
- `Other`: You can easily implement your own by extending aiocache.Serializer


### Clocks

A clock is used to measure elapsed time since a value was added into the cache, possibly triggering its eviction.

You can specify a clock when instantiating a cache. e.g., `DictCache(clock=TestClock())`

#### API

- `def now(self)`: Measures the current time, in seconds
- `async def sleep(self, n)`: Awaits until `n` seconds have elapsed

#### Implementations

- `SystemClock` (**default**): This measures real-world time, based on `time.time()`
- `TestClock`: This is useful for unit-tests: Ignores real-world time and immediately advances the current time when calling `await clock.sleep(t)`
