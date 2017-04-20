import asyncio
from aiohttp import web
import aiohttp_tokio as tokio


if __name__ == '__main__':
    evloop = tokio.new_event_loop()

    app = tokio.Application(debug=False, handler_args={'access_log': None})
    async def handler(req):
        return web.Response()

    app.router.add_get('/', handler)
    handler = app.make_handler(loop=evloop)

    server = evloop.create_http_server(handler, host="127.0.0.1", port=9090)

    print('starting', evloop.time())
    evloop.run_forever()
    evloop.close()
