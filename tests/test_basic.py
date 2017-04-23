import asyncio
import traceback
import os
import aiohttp
from aiohttp import web

import aiohttp_tokio as tokio


def stop_event_loop(name, evloop, *args):
    print('stop_event_loop from: %s' % name, evloop, args)
    print(evloop.stop())


def cb2(name, handle, evloop):
    print('callback2: %s' % name, handle, 'running:', evloop.is_running())
    print(handle.cancel())
    print('callback2: %s' % name, evloop.stop(), evloop.time())


def test_call_later():
    name = 'test_call_later'
    evloop = tokio.new_event_loop()
    handle = evloop.call_later(1.0, stop_event_loop, name, evloop)
    evloop.call_later(0.5, cb2, name, handle, evloop)

    print(evloop, evloop.time())
    print('starting')
    evloop.run_forever()
    evloop.close()


def test_call_at():
    name = 'test_call_at'
    evloop = tokio.new_event_loop()
    time = evloop.time()

    handle = evloop.call_at(time + 1.0, stop_event_loop, name, evloop)
    evloop.call_at(time + 0.5, cb2, name, handle, evloop)

    print(evloop, evloop.time())
    evloop.run_forever()
    evloop.close()


def test_call_soon():
    name = 'test_call_soon'
    evloop = tokio.new_event_loop()

    evloop.call_soon(stop_event_loop, name, evloop)

    print('starting:', name, evloop, evloop.time())
    evloop.run_forever()
    evloop.close()


def create_fut(evloop):
    fut = evloop.create_future()
    fut.add_done_callback(cb_fut_res)
    evloop.call_later(0.5, cb_fut, 'call_later:fut', fut)


def cb_fut(name, fut):
    print(name, fut)
    fut.set_result(1)


def cb_fut_res(fut):
    print('future completed:', fut.result())


def test_future():
    evloop = tokio.new_event_loop()
    evloop.call_later(0.1, create_fut, evloop)
    evloop.call_later(2.0, stop_event_loop, 'test_future', evloop)

    print(evloop, evloop.time())
    print('starting')
    evloop.run_forever()
    evloop.close()
    print('done')


def test_future_exc():
    name = "test_future_exc"

    def create_fut(evloop):
        fut = evloop.create_future()

        try:
            fut.result()
        except Exception as exc:
            traceback.print_exc()
            print(repr(exc))

        fut.add_done_callback(cb_fut_res)
        fut.set_exception(ValueError())
        evloop.call_later(0.5, cb_fut, fut)

    def cb_fut(fut):
        print(name, fut)
        fut.set_result(1)

    def cb_fut_res(fut):
        print('future completed:', repr(fut.exception()))
        fut.result()

    evloop = tokio.new_event_loop()
    evloop.call_later(0.01, create_fut, evloop)
    evloop.call_later(2.0, stop_event_loop, name, evloop)

    print(evloop, evloop.time())
    print('starting')
    evloop.run_forever()
    evloop.close()


def test_task():
    name = 'test_task'
    counter = 0
    evloop = tokio.new_event_loop()

    async def coro():
        nonlocal counter
        while True:
            counter += 1
            print('coro', counter)
            await asyncio.sleep(0.2, loop=evloop)

    def start(evloop):
        asyncio.ensure_future(coro(), loop=evloop)

    evloop.call_later(0.01, start, evloop)
    evloop.call_later(3.0, stop_event_loop, name, evloop)

    print(evloop, evloop.time())
    print('starting')
    evloop.run_forever()
    evloop.close()


def test_task2():
    name = 'test_task'
    counter = 0
    evloop = tokio.new_event_loop()

    def coro(fut):
        res = yield from fut
        print("Done: %s", res)
        evloop.stop()

    def start(evloop):
        fut = evloop.create_future()
        asyncio.ensure_future(coro(fut), loop=evloop)
        evloop.call_later(0.01, fut.set_result, 1)

    evloop.call_later(0.01, start, evloop)
    #evloop.call_later(3.0, stop_event_loop, name, evloop)

    print(evloop, evloop.time())
    print('starting')
    evloop.run_forever()
    evloop.close()


def test_task3():
    name = 'test_task'
    counter = 0
    evloop = tokio.new_event_loop()

    async def coro(fut):
        res = await fut
        print("Done: %s" % res)

    def start(evloop):
        fut = evloop.create_future()
        asyncio.ensure_future(coro(fut), loop=evloop)
        evloop.call_later(0.01, fut.set_result, 1)

    evloop.call_later(0.01, start, evloop)
    evloop.call_later(3.0, stop_event_loop, name, evloop)

    print(evloop, evloop.time())
    print('starting')
    evloop.run_forever()
    evloop.close()


def test_run_until_complete():
    name = 'test_run_until_complete'
    counter = 0
    evloop = tokio.new_event_loop()

    async def coro():
        nonlocal counter
        while True:
            counter += 1
            if counter > 5:
                return

            print('%s: iteration' % name, counter)
            await asyncio.sleep(0.2, loop=evloop)

    task = asyncio.ensure_future(coro(), loop=evloop)

    print('starting', evloop.time())
    evloop.run_until_complete(task)
    evloop.close()


def test_create_server():
    name = 'test_create_server'
    evloop = tokio.new_event_loop()

    async def coro():
        try:
            res = evloop.create_server(None, host="127.0.0.1", port=9090)
            print(res)
        except:
            import traceback
            traceback.print_exc()

        await asyncio.sleep(2, loop=evloop)
        res.close()
        await asyncio.sleep(0.1, loop=evloop)

    task = asyncio.ensure_future(coro(), loop=evloop)

    print('starting', evloop.time())
    evloop.run_until_complete(task)
    evloop.close()


def test_web():
    name = 'test_web'
    evloop = tokio.new_event_loop()

    app = tokio.Application(debug=False, handler_args={'access_log': None})
    async def handler(req):
        return web.Response()

    app.router.add_get('/', handler)
    handler = app.make_handler(loop=evloop)

    server = evloop.create_http_server(handler, host="127.0.0.1", port=9090)
    evloop.call_later(6000.0, stop_event_loop, name, evloop)

    print('starting', evloop.time())
    evloop.run_forever()
    evloop.close()


async def client(loop):
    session = aiohttp.ClientSession(loop=loop)
    resp = await session.request('get', 'http://python.org', timeout=0)
    content = await resp.read()
    print(content)
    session.close()


def test_client():
    evloop = tokio.new_event_loop()

    print('starting', evloop.time())
    task = asyncio.ensure_future(client(evloop), loop=evloop)
    evloop.run_until_complete(task)
    evloop.close()
