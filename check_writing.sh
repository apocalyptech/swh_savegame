#!/bin/bash
# vim: set expandtab tabstop=4 shiftwidth=4:

# Verify that we understand the format of all the savegames in the current dir
# (and write out the next bit of unparsed data as a hexdump)

for file in savegame_00*.dat
do
    echo $file
    ./save.py -c $file -vv
done
