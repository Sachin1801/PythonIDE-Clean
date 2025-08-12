#!/usr/bin/env python3
from common.msg import res_put


async def response(client, id, code=0, data=None):
    msg = {
        'type': 'response',
        'id': id,
        'code': code,
        'data': data
    }
    await res_put(client, msg)

