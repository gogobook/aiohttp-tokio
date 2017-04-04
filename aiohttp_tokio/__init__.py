import asyncio  # noqa
from . import patch
from . import _aiohttp

patch.patch_asyncio()


__all__ = ('new_event_loop', 'EventLoopPolicy')


def new_event_loop():
    return _aiohttp.new_event_loop()


def spawn_event_loop(name='event-loop'):
    return _aiohttp.spawn_event_loop(name)


class EventLoopPolicy:
    """Event loop policy."""

    def _loop_factory(self):
        return new_event_loop()
