import asyncio
from aiohttp import web, hdrs
from aiohttp.helpers import TimeService
from aiohttp.web_request import BaseRequest

from .web_protocol import RequestHandler
from .web_urldispatcher import UrlDispatcher


class Application(web.Application):

    @asyncio.coroutine
    def _handle(self, request):
        match_info = yield from self._router.resolve(request)
        match_info.add_app(self)

        if __debug__:
            match_info.freeze()

        resp = None
        request.match_info = match_info
        expect = request.headers.get(hdrs.EXPECT)
        if expect:
            resp = (
                yield from match_info.expect_handler(request))

        if resp is None:
            handler = match_info.handler
            for app in match_info.apps:
                for factory in app._middlewares:
                    handler = yield from factory(app, handler)

            resp = yield from handler(request)

        return resp

    def make_handler(self, *, loop=None,
                     secure_proxy_ssl_header=None, **kwargs):
        self._set_loop(loop)
        self.freeze()

        kwargs['debug'] = self.debug
        if self._handler_args:
            for k, v in self._handler_args.items():
                kwargs[k] = v

        self._secure_proxy_ssl_header = secure_proxy_ssl_header
        return Server(self._handle, request_factory=self._make_request,
                      loop=self.loop, **kwargs)


class Server:

    factory = RequestHandler

    def __init__(self, handler, *, request_factory=None, loop=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop
        self._connections = {}
        self._kwargs = kwargs
        self.time_service = TimeService(self._loop)
        self.requests_count = 0
        self.request_handler = handler
        self.request_factory = request_factory or self._make_request

    @property
    def connections(self):
        return list(self._connections.keys())

    def connection_made(self, handler, transport):
        self._connections[handler] = transport

    def connection_lost(self, handler, exc=None):
        if handler in self._connections:
            del self._connections[handler]

    def _make_request(self, message, payload, protocol, writer, task):
        return BaseRequest(
            message, payload, protocol, writer,
            protocol.time_service, task)

    @asyncio.coroutine
    def shutdown(self, timeout=None):
        coros = [conn.shutdown(timeout) for conn in self._connections]
        yield from asyncio.gather(*coros, loop=self._loop)
        self._connections.clear()
        self.time_service.close()

    finish_connections = shutdown

    def __call__(self):
        return self.factory(self, loop=self._loop, **self._kwargs)
