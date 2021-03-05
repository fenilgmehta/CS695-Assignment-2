import struct
import json

json.load(open('message.conf'))

result = ''

# big-endian format and 2 bytes (unsigned short)
int.from_bytes(result[:2], "big")
