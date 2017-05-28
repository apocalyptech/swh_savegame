#!/usr/bin/env python
# vim: set expandtab tabstop=4 shiftwidth=4:

import sys
import struct
import binascii

# Fixes the checksum of a passed-in savegame, useful if you've done
# any direct hex editing on a savegame file

if len(sys.argv) != 2:
    print('Pass in a savegame as the first argument')
    sys.exit(1)

savefile = sys.argv[1]
print('Operating on savefile {}'.format(savefile))

with open(savefile, 'r+b') as df:
    data = df.read()
    (on_disk_checksum,) = struct.unpack('I', data[1:5])
    print('Checksum in the file itself: {}'.format(hex(on_disk_checksum)))
    new_checksum = binascii.crc32(data[5:])
    if new_checksum == on_disk_checksum:
        print('Checksum is correct, exiting.')
        sys.exit(0)
    print('Correct checksum: {}'.format(hex(new_checksum)))

    df.seek(1)
    df.write(struct.pack('I', new_checksum))
    print('Wrote corrected checksum')
