import asyncio
import importlib.util
from asyncio import AbstractEventLoop
from typing import Optional

from okdmr.protocols.mmdvm2020.server_protocol import Mmdvm2020ServerProtocol


class OkdmrMaster:
    def __init__(self):
        self.loop: Optional[AbstractEventLoop] = None

    async def start(self):
        self.loop = asyncio.get_running_loop()
        await self.loop.create_datagram_endpoint(
            lambda: Mmdvm2020ServerProtocol(),
            local_addr=("0.0.0.0", 62031)
        )


if __name__ == "__main__":

    uvloop_spec = importlib.util.find_spec("uvloop")
    if uvloop_spec:
        import uvloop

        uvloop.install()

    loop = asyncio.get_event_loop()
    master = OkdmrMaster()

    loop.run_until_complete(master.start())
    loop.run_forever()
