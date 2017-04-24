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


def _GatheringFuture(children, *, loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()

    fut = loop.create_future()

    def cancel(fut):
        if fut.cancelled():
            for child in children:
                if child.cancel():
                    ret = True
            return ret

    fut.add_done_callback(cancel)
    return fut


def patch_asyncio():
    asyncio.sleep.__code__ = sleep.__code__
    asyncio.tasks._GatheringFuture = _GatheringFuture
