import asyncio
from asyncio import tasks


@asyncio.coroutine
def sleep(delay, result=None, *, loop=None):
    """Coroutine that completes after a given time (in seconds)."""
    if delay == 0:
        yield
        return result

    if loop is None:
        loop = events.get_event_loop()

    future = loop.create_future()
    h = loop.call_later(delay,
                        futures._set_result_unless_cancelled,
                        future, result)
    try:
        return (yield from future)
    finally:
        h.cancel()


def patch_asyncio():
    asyncio.sleep.__code__ = sleep.__code__
