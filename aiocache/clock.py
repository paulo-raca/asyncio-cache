import asyncio
from time import time

class Clock:
    """
    Abstraction measuring elapsed time and waiting
    """
    def now(self):
        """ Measure the current time, in seconds """
        raise NotImplemented()

    async def sleep(self, n):
        """ Waits until the specified amount of time has elapsed """
        raise NotImplemented()


class SystemClock:
    def now(self):
        return time()

    async def sleep(self, n):
        await asyncio.sleep(n)


class TestClock:
    def __init__(self):
        self.t = 0

    def now(self):
        return self.t

    async def sleep(self, n):
        self.t += n
