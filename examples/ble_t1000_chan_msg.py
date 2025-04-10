#!/usr/bin/python

import asyncio
import json
from meshcore import MeshCore
from meshcore import BLEConnection

ADDRESS = "t1000" # node ble adress or name
DEST = "mchome"
MSG = "Hello World"

async def main () :
    con  = BLEConnection(ADDRESS)
    await con.connect()
    mc = MeshCore(con)
    await mc.connect()

    await mc.send_chan_msg(0, MSG)

asyncio.run(main())
