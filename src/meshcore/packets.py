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
    CONTACT_URI = 11
    BATTERY = 12
    DEVICE_INFO = 13
    PRIVATE_KEY = 14
    DISABLED = 15
    CONTACT_MSG_RECV_V3 = 16
    CHANNEL_MSG_RECV_V3 = 17
    CHANNEL_INFO = 18
    SIGN_START = 19
    SIGNATURE = 20
    CUSTOM_VARS = 21
    BINARY_REQ = 50
    FACTORY_RESET = 51
    
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
    TRACE_DATA = 0x89
    PUSH_CODE_NEW_ADVERT = 0x8A
    TELEMETRY_RESPONSE = 0x8B
    BINARY_RESPONSE = 0x8C
    PATH_DISCOVERY_RESPONSE = 0x8D
