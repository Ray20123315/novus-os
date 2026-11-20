#!/usr/bin/env python3
"""Compare the inode-table block against a captured smoke-test sample."""
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'out', 'novus.img')
BLOCK_OFFSET = 130 * 4096

with open(IMAGE, 'rb') as fh:
    fh.seek(BLOCK_OFFSET)
    data = fh.read(4096)
if len(data) != 4096:
    raise ValueError('NovusFS image is truncated before block 130 ends')

print('file block130[0:16]:', data[:16].hex())
print('file block130[128:144] (inode2 word0/size):', data[128:144].hex())
print('smoke tmp-b130 p0=0x48DBBF0F48DA29F2 p1=0xBF0F48C8394CD829')
sm0 = 0x48DBBF0F48DA29F2
sm1 = 0xBF0F48C8394CD829
sb = struct.pack('<QQ', sm0, sm1)
print('smoke tmp-b130 bytes LE:', sb.hex())
print('MATCH block130[0:16]?', data[:16] == sb)
for i in range(0, 128, 8):
    print('ino off', i, struct.unpack_from('<Q', data, i)[0])
