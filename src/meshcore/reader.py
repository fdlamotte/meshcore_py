import sys
import logging
import asyncio
from typing import Any, Optional, Dict
from .events import Event, EventType, EventDispatcher
from .packets import PacketType

logger = logging.getLogger("meshcore")


class MessageReader:
    def __init__(self, dispatcher: EventDispatcher):
        self.dispatcher = dispatcher
        # We're only keeping state here that's needed for processing
        # before events are dispatched
        self.contacts = {}  # Temporary storage during contact list building
        self.contact_nb = 0  # Used for contact processing
        
    async def handle_rx(self, data: bytearray):
        packet_type_value = data[0]
        logger.debug(f"Received data: {data.hex()}")
        
        # Handle command responses
        if packet_type_value == PacketType.OK.value:
            result = None
            if len(data) == 5:
                result = int.from_bytes(data[1:5], byteorder='little')
            else:
                result = True
                
            # Dispatch event for the OK response
            await self.dispatcher.dispatch(Event(EventType.OK, result))
            
        elif packet_type_value == PacketType.ERROR.value:
            result = False
            if len(data) > 1:
                result = {"error_code": data[1]}
            
            # Dispatch event for the ERROR response
            await self.dispatcher.dispatch(Event(EventType.ERROR, result))
            
        elif packet_type_value == PacketType.CONTACT_START.value:
            self.contact_nb = int.from_bytes(data[1:5], byteorder='little')
            self.contacts = {}
            
        elif packet_type_value == PacketType.CONTACT.value:
            c = {}
            c["public_key"] = data[1:33].hex()
            c["type"] = data[33]
            c["flags"] = data[34]
            c["out_path_len"] = int.from_bytes(data[35:36], signed=True)
            plen = int.from_bytes(data[35:36], signed=True)
            if plen == -1:
                plen = 0
            c["out_path"] = data[36:36+plen].hex()
            c["adv_name"] = data[100:132].decode().replace("\0","")
            c["last_advert"] = int.from_bytes(data[132:136], byteorder='little')
            c["adv_lat"] = int.from_bytes(data[136:140], byteorder='little',signed=True)/1e6
            c["adv_lon"] = int.from_bytes(data[140:144], byteorder='little',signed=True)/1e6
            c["lastmod"] = int.from_bytes(data[144:148], byteorder='little')
            self.contacts[c["public_key"]] = c
            
        elif packet_type_value == PacketType.CONTACT_END.value:
            await self.dispatcher.dispatch(Event(EventType.CONTACTS, self.contacts))
            
            
        elif packet_type_value == PacketType.SELF_INFO.value:
            self_info = {}
            self_info["adv_type"] = data[1]
            self_info["tx_power"] = data[2]
            self_info["max_tx_power"] = data[3]
            self_info["public_key"] = data[4:36].hex()
            self_info["adv_lat"] = int.from_bytes(data[36:40], byteorder='little', signed=True)/1e6
            self_info["adv_lon"] = int.from_bytes(data[40:44], byteorder='little', signed=True)/1e6
            self_info["radio_freq"] = int.from_bytes(data[48:52], byteorder='little') / 1000
            self_info["radio_bw"] = int.from_bytes(data[52:56], byteorder='little') / 1000
            self_info["radio_sf"] = data[56]
            self_info["radio_cr"] = data[57]
            self_info["name"] = data[58:].decode()
            await self.dispatcher.dispatch(Event(EventType.SELF_INFO, self_info))
            
        elif packet_type_value == PacketType.MSG_SENT.value:
            res = {}
            res["type"] = data[1]
            res["expected_ack"] = bytes(data[2:6])
            res["suggested_timeout"] = int.from_bytes(data[6:10], byteorder='little')
            await self.dispatcher.dispatch(Event(EventType.MSG_SENT, res))
            
        elif packet_type_value == PacketType.CONTACT_MSG_RECV.value:
            res = {}
            res["type"] = "PRIV"
            res["pubkey_prefix"] = data[1:7].hex()
            res["path_len"] = data[7]
            res["txt_type"] = data[8]
            res["sender_timestamp"] = int.from_bytes(data[9:13], byteorder='little')
            if data[8] == 2:
                res["signature"] = data[13:17].hex()
                res["text"] = data[17:].decode()
            else:
                res["text"] = data[13:].decode()
            await self.dispatcher.dispatch(Event(EventType.CONTACT_MSG_RECV, res))
            
        elif packet_type_value == 16:  # A reply to CMD_SYNC_NEXT_MESSAGE (ver >= 3)
            res = {}
            res["type"] = "PRIV"
            res["SNR"] = int.from_bytes(data[1:2], byteorder='little', signed=True) * 4
            res["pubkey_prefix"] = data[4:10].hex()
            res["path_len"] = data[10]
            res["txt_type"] = data[11]
            res["sender_timestamp"] = int.from_bytes(data[12:16], byteorder='little')
            if data[11] == 2:
                res["signature"] = data[16:20].hex()
                res["text"] = data[20:].decode()
            else:
                res["text"] = data[16:].decode()
            await self.dispatcher.dispatch(Event(EventType.CONTACT_MSG_RECV, res, {"extended": True}))
            
        elif packet_type_value == PacketType.CHANNEL_MSG_RECV.value:
            res = {}
            res["type"] = "CHAN"
            res["channel_idx"] = data[1]
            res["path_len"] = data[2]
            res["txt_type"] = data[3]
            res["sender_timestamp"] = int.from_bytes(data[4:8], byteorder='little')
            res["text"] = data[8:].decode()
            await self.dispatcher.dispatch(Event(EventType.CHANNEL_MSG_RECV, res))
            
        elif packet_type_value == 17:  # A reply to CMD_SYNC_NEXT_MESSAGE (ver >= 3)
            res = {}
            res["type"] = "CHAN"
            res["SNR"] = int.from_bytes(data[1:2], byteorder='little', signed=True) * 4
            res["channel_idx"] = data[4]
            res["path_len"] = data[5]
            res["txt_type"] = data[6]
            res["sender_timestamp"] = int.from_bytes(data[7:11], byteorder='little')
            res["text"] = data[11:].decode()
            await self.dispatcher.dispatch(Event(EventType.CHANNEL_MSG_RECV, res, {"extended": True}))
            
        elif packet_type_value == PacketType.CURRENT_TIME.value:
            result = int.from_bytes(data[1:5], byteorder='little')
            await self.dispatcher.dispatch(Event(EventType.CURRENT_TIME, result))
            
        elif packet_type_value == PacketType.NO_MORE_MSGS.value:
            await self.dispatcher.dispatch(Event(EventType.NO_MORE_MSGS, False))
            
        elif packet_type_value == PacketType.CONTACT_SHARE.value:
            result = "meshcore://" + data[1:].hex()
            await self.dispatcher.dispatch(Event(EventType.CONTACT_SHARE, result))
            
        elif packet_type_value == PacketType.BATTERY.value:
            result = int.from_bytes(data[1:3], byteorder='little')
            await self.dispatcher.dispatch(Event(EventType.BATTERY, result))
            
        elif packet_type_value == PacketType.DEVICE_INFO.value:
            res = {}
            res["fw ver"] = data[1]
            if data[1] >= 3:
                res["max_contacts"] = data[2] * 2
                res["max_channels"] = data[3]
                res["ble_pin"] = int.from_bytes(data[4:8], byteorder='little')
                res["fw_build"] = data[8:20].decode().replace("\0","")
                res["model"] = data[20:60].decode().replace("\0","")
                res["ver"] = data[60:80].decode().replace("\0","")
            await self.dispatcher.dispatch(Event(EventType.DEVICE_INFO, res))
            
        elif packet_type_value == PacketType.CLI_RESPONSE.value:
            res = {}
            res["response"] = data[1:].decode()
            await self.dispatcher.dispatch(Event(EventType.CLI_RESPONSE, res))
            
        # Push notifications
        elif packet_type_value == PacketType.ADVERTISEMENT.value:
            logger.debug("Advertisement received")
            # todo: Read advertisement?
            await self.dispatcher.dispatch(Event(EventType.ADVERTISEMENT, None))
            
        elif packet_type_value == PacketType.PATH_UPDATE.value:
            logger.debug("Code path update")
            await self.dispatcher.dispatch(Event(EventType.PATH_UPDATE, None))
            
        elif packet_type_value == PacketType.ACK.value:
            logger.debug("Received ACK")
            await self.dispatcher.dispatch(Event(EventType.ACK, None))
            
        elif packet_type_value == PacketType.MESSAGES_WAITING.value:
            logger.debug("Msgs are waiting")
            await self.dispatcher.dispatch(Event(EventType.MESSAGES_WAITING, None))
            
        elif packet_type_value == PacketType.RAW_DATA.value:
            res = {}
            res["SNR"] = data[1] / 4
            res["RSSI"] = data[2]
            res["payload"] = data[4:].hex()
            logger.debug("Received raw data")
            print(res)
            await self.dispatcher.dispatch(Event(EventType.RAW_DATA, res))
            
        elif packet_type_value == PacketType.LOGIN_SUCCESS.value:
            logger.debug("Login success")
            await self.dispatcher.dispatch(Event(EventType.LOGIN_SUCCESS, None))
            
        elif packet_type_value == PacketType.LOGIN_FAILED.value:
            logger.debug("Login failed")
            await self.dispatcher.dispatch(Event(EventType.LOGIN_FAILED, None))
            
        elif packet_type_value == PacketType.STATUS_RESPONSE.value:
            res = {}
            res["pubkey_pre"] = data[2:8].hex()
            res["bat"] = int.from_bytes(data[8:10], byteorder='little')
            res["tx_queue_len"] = int.from_bytes(data[10:12], byteorder='little')
            res["free_queue_len"] = int.from_bytes(data[12:14], byteorder='little')
            res["last_rssi"] = int.from_bytes(data[14:16], byteorder='little', signed=True)
            res["nb_recv"] = int.from_bytes(data[16:20], byteorder='little', signed=False)
            res["nb_sent"] = int.from_bytes(data[20:24], byteorder='little', signed=False)
            res["airtime"] = int.from_bytes(data[24:28], byteorder='little')
            res["uptime"] = int.from_bytes(data[28:32], byteorder='little')
            res["sent_flood"] = int.from_bytes(data[32:36], byteorder='little')
            res["sent_direct"] = int.from_bytes(data[36:40], byteorder='little')
            res["recv_flood"] = int.from_bytes(data[40:44], byteorder='little')
            res["recv_direct"] = int.from_bytes(data[44:48], byteorder='little')
            res["full_evts"] = int.from_bytes(data[48:50], byteorder='little')
            res["last_snr"] = int.from_bytes(data[50:52], byteorder='little', signed=True) / 4
            res["direct_dups"] = int.from_bytes(data[52:54], byteorder='little')
            res["flood_dups"] = int.from_bytes(data[54:56], byteorder='little')
            data_hex = data[8:].hex()
            logger.debug(f"Status response: {data_hex}")
            await self.dispatcher.dispatch(Event(EventType.STATUS_RESPONSE, res))
            
        elif packet_type_value == PacketType.LOG_DATA.value:
            logger.debug("Received log data")
            await self.dispatcher.dispatch(Event(EventType.LOG_DATA, data[1:].decode('utf-8', errors='replace')))
            
        else:
            logger.debug(f"Unhandled data received {data}")
            logger.debug(f"Unhandled packet type: {packet_type_value}")