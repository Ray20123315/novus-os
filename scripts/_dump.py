import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'out', 'novus.img')
with open(path, 'rb') as fh:
    data = fh.read()
itbl = struct.unpack_from('<Q', data, 24)[0]
print('itbl', itbl)
b = (2 - 1) // 32 + itbl

off = ((2 - 1) % 32) * 128

bo = b * 4096 + off
inb = data[bo:bo + 128]
print('inode2 bytes:', inb.hex())
for i in range(0, 128, 8):
    print(i, struct.unpack_from('<Q', inb, i)[0])
