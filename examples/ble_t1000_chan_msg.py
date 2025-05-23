#!/usr/bin/python

import asyncio
import json
from meshcore import MeshCore
from meshcore import BLEConnection

ADDRESS = "echo" # node ble adress or name
DEST = "mchome"
MSG = "Hello World"

async def main () :
    con  = BLEConnection(ADDRESS)
    await con.connect()
    mc = MeshCore(con)
    await mc.connect()

    await mc.commands.send_chan_msg(0, MSG)

asyncio.run(main())
