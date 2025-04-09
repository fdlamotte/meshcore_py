from enum import Enum

# Packet prefixes for the protocol
class PacketType(Enum):
    OK = 0
    ERROR = 1
    CONTACT_START = 2
    CONTACT = 3
    CONTACT_END = 4
    SELF_INFO = 5
    MSG_SENT = 6
    CONTACT_MSG_RECV = 7
    CHANNEL_MSG_RECV = 8
    CURRENT_TIME = 9
    NO_MORE_MSGS = 10
    CONTACT_SHARE = 11
    BATTERY = 12
    DEVICE_INFO = 13
    CLI_RESPONSE = 50
    
    # Push notifications
    ADVERTISEMENT = 0x80
    PATH_UPDATE = 0x81
    ACK = 0x82
    MESSAGES_WAITING = 0x83
    RAW_DATA = 0x84
    LOGIN_SUCCESS = 0x85
    LOGIN_FAILED = 0x86
    STATUS_RESPONSE = 0x87
    LOG_DATA = 0x88