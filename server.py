import struct
import json

json.load(open('message.conf'))

# big-endian format and 2 bytes (unsigned short)
struct.pack(">H", 12)  # max value can be 65535
