#!/usr/bin/env python
# vim: set expandtab tabstop=4 shiftwidth=4:
#
# Copyright (c) 2017, CJ Kucera
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the development team nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL CJ KUCERA BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import io
import sys
import struct
import string
import binascii
import argparse
import collections

def read_uint8(df):
    return struct.unpack('B', df.read(1))[0]

def write_uint8(df, value):
    df.write(struct.pack('B', value))

def read_uint16(df):
    return struct.unpack('H', df.read(2))[0]

def write_uint16(df, value):
    df.write(struct.pack('H', value))

def read_uint32(df):
    return struct.unpack('I', df.read(4))[0]

def write_uint32(df, value):
    df.write(struct.pack('I', value))

def read_string(df):
    strlen = read_uint8(df)
    return df.read(strlen)

def write_string(df, value):
    write_uint8(df, len(value))
    df.write(value)

def read_uint8list(df):
    uint8s = []
    for num in range(read_uint8(df)):
        uint8s.append(read_uint8(df))
    return uint8s

def write_uint8list(df, uint8s):
    write_uint8(df, len(uint8s))
    for value in uint8s:
        write_uint8(df, value)

def read_uint32list(df):
    uint32s = []
    for num in range(read_uint8(df)):
        uint32s.append(read_uint32(df))
    return uint32s

def write_uint32list(df, uint32s):
    write_uint8(df, len(uint32s))
    for value in uint32s:
        write_uint32(df, value)

def read_stringlist(df):
    strings = []
    for num in range(read_uint8(df)):
        strings.append(read_string(df))
    return strings

def write_stringlist(df, strings):
    write_uint8(df, len(strings))
    for value in strings:
        write_string(df, value)

class Character(object):
    """
    Class for holding some info about a character.  For playable characters,
    the 'attributes' dict will end up containing two items: 'starting' and
    'upgrades'.  'starting' appears to always be zero, whereas 'upgrades' is
    the character's current XP.  Note that *just* setting a high XP level does
    not actually activate character abilities; those get unlocked elsewhere
    in the file.
    """

    def __init__(self, name):
        self.name = name
        self.other_name = name
        self.unknown_1 = 0
        self.attributes = collections.OrderedDict()

        # This attribute is only really used for player
        # chars, and is assigned later on in the file.
        self.idnum = None

    @staticmethod
    def read_chars(df):
        """
        Reads player character information from a file.  Returns an OrderedDict
        of all characters found, with their names as the keys.
        """
        characters = collections.OrderedDict()
        num_chars = read_uint8(df)
        for num in range(num_chars):

            # Read in the initial name and add to our dict
            name = read_string(df)
            char = Character(name)
            characters[name] = char

            # I suspect this is actually an attribute list like the
            # next one, but used for statuses while inside a level.
            # (health, quantity of abilities remaining, etc)
            char.unknown_1 = read_uint8(df)
            assert char.unknown_1 == 0

            # List of attributes
            num_attrs = read_uint8(df)
            for attrnum in range(num_attrs):
                name = read_string(df)
                value = read_uint32(df)
                char.attributes[name] = value

            # And then the name repeats for some reason
            char.other_name = read_string(df)

        return characters

    @staticmethod
    def write_chars(df, charlist):
        """
        Write player characters to a file
        """
        write_uint8(df, len(charlist))
        for char in charlist.values():
            write_string(df, char.name)
            write_uint8(df, char.unknown_1)
            write_uint8(df, len(char.attributes))
            for (name, value) in char.attributes.items():
                write_string(df, name)
                write_uint32(df, value)
            write_string(df, char.other_name)

class Objective(object):
    """
    No real idea what any of this is.
    """

    def __init__(self):
        self.byte_01 = 0
        self.name = ''
        self.int_01 = 0
        self.int_02 = 0
        self.zero_01 = 0
        self.zero_02 = 0
        self.zero_03 = 0
        self.int_list = []
        self.short_01 = 0
        self.byte_02 = 0
        self.int_03 = 0
        self.short_02 = 0

    @staticmethod
    def read_objectives(df):
        """
        Reads information from a file.  Returns a list
        """

        objectives = []
        num_objectives = read_uint8(df)
        for num in range(num_objectives):

            # Create an object and read everything in.  Will assert
            # on a few things we think are true
            obj = Objective()
            objectives.append(obj)

            obj.byte_01 = read_uint8(df)
            assert obj.byte_01 == 0

            obj.name = read_string(df)

            obj.int_01 = read_uint32(df)
            obj.int_02 = read_uint32(df)

            obj.zero_01 = read_uint32(df)
            assert obj.zero_01 == 0
            obj.zero_02 = read_uint32(df)
            assert obj.zero_02 == 0
            obj.zero_03 = read_uint32(df)
            assert obj.zero_03 == 0

            obj.int_list = read_uint32list(df)

            obj.short_01 = read_uint16(df)
            obj.byte_02 = read_uint8(df)
            obj.int_03 = read_uint32(df)
            obj.short_02 = read_uint16(df)

        return objectives

    @staticmethod
    def write_objectives(df, objectives):
        """
        Write to a file
        """
        write_uint8(df, len(objectives))
        for obj in objectives:
            write_uint8(df, obj.byte_01)
            write_string(df, obj.name)
            write_uint32(df, obj.int_01)
            write_uint32(df, obj.int_02)
            write_uint32(df, obj.zero_01)
            write_uint32(df, obj.zero_02)
            write_uint32(df, obj.zero_03)
            write_uint32list(df, obj.int_list)
            write_uint16(df, obj.short_01)
            write_uint8(df, obj.byte_02)
            write_uint32(df, obj.int_03)
            write_uint16(df, obj.short_02)

class Mission(object):
    """
    I actually don't know if this are missions exactly, or
    checkpoints or something.
    """

    def __init__(self, name):
        self.name = name
        self.bytelist = []
        self.unknown_03 = 0
        self.unknown_04 = 0
        self.other_name = name
        self.objectives = []

    @staticmethod
    def read_missions(df):
        """
        Reads information from a file.  Returns an OrderedDict
        of all missions/whatever found, with their names as the
        keys.
        """
        missions = collections.OrderedDict()
        num_missions = read_uint8(df)
        for num in range(num_missions):

            # Read in the initial name and add to our dict
            name = read_string(df)
            mission = Mission(name)
            missions[name] = mission

            # A list of bytes, apparently.  Shows up as just
            # "01 01" for most missions, but found at least one
            # "02 01 01"
            mission.bytelist = read_uint8list(df)

            # The name again, apparently
            mission.other_name = read_string(df)

            # No idea about these four
            mission.unknown_03 = read_uint8(df)
            mission.unknown_04 = read_uint8(df)

            # Objectives, I guess
            mission.objectives = Objective.read_objectives(df)

        return missions

    @staticmethod
    def write_missions(df, missions):
        """
        Write to a file
        """
        write_uint8(df, len(missions))
        for mission in missions.values():
            write_string(df, mission.name)
            write_uint8list(df, mission.bytelist)
            write_string(df, mission.other_name)
            write_uint8(df, mission.unknown_03)
            write_uint8(df, mission.unknown_04)
            Objective.write_objectives(df, mission.objectives)

class Level(object):
    """
    I actually don't know if this are levels exactly
    """

    def __init__(self, name):
        self.name = name
        self.unknown_01 = 0
        self.intlist = []
        self.unknown_02 = 0
        self.unknown_03 = 0
        self.unknown_04 = 0
        self.unknown_05 = 0

    @staticmethod
    def read_levels(df):
        """
        Reads information from a file.  Returns an OrderedDict
        of all levels/whatever found, with their names as the
        keys.
        """
        levels = collections.OrderedDict()
        num_levels = read_uint8(df)
        for num in range(num_levels):

            # Read in the initial name and add to our dict
            name = read_string(df)
            level = Level(name)
            levels[name] = level

            # All unknown, basically.  I'm sure that one of
            # these is the number of stars acquired on the level,
            # perhaps even by difficulty level or something.
            # Perhaps that's what that uint32list is, actually...
            level.unknown_01 = read_uint8(df)
            level.intlist = read_uint32list(df)
            level.unknown_02 = read_uint8(df)
            level.unknown_03 = read_uint8(df)
            level.unknown_04 = read_uint32(df)
            level.unknown_05 = read_uint32(df)

        return levels

    @staticmethod
    def write_levels(df, levels):
        """
        Write to a file
        """
        write_uint8(df, len(levels))
        for level in levels.values():
            write_string(df, level.name)
            write_uint8(df, level.unknown_01)
            write_uint32list(df, level.intlist)
            write_uint8(df, level.unknown_02)
            write_uint8(df, level.unknown_03)
            write_uint32(df, level.unknown_04)
            write_uint32(df, level.unknown_05)

class Item(object):
    """
    Class to hold information about an item (also applies to hats)
    """

    def __init__(self, name, idnum):
        self.name = name
        self.idnum = idnum

    @staticmethod
    def read_items(df):
        """
        Reads item information from a file.  Returns an OrderedDict
        of all characters found, with their ID numbers as the keys.
        """
        items = collections.OrderedDict()
        num_items = read_uint8(df)
        for num in range(num_items):

            # Read in the initial name and add to our dict
            idnum = read_uint32(df)
            name = read_string(df)
            item = Item(name=name, idnum=idnum)
            items[idnum] = item

        return items

    @staticmethod
    def write_items(df, items):
        """
        Write items to a file
        """
        write_uint8(df, len(items))
        for item in items.values():
            write_uint32(df, item.idnum)
            write_string(df, item.name)

class Pickup(object):
    """
    Class to hold information about pickups
    """

    def __init__(self, name):
        self.name = name
        self.locations = collections.OrderedDict() 
        self.unknown_01 = 0
        self.unknown_02 = 0

    @staticmethod
    def read_pickups(df):
        """
        Reads pickup information from a file.  Returns an OrderedDict
        of all pickups found, with their names as the keys.
        """
        pickups = collections.OrderedDict()
        num_pickups = read_uint8(df)
        for num_pickup in range(num_pickups):

            name = read_string(df)
            pickup = Pickup(name=name)
            pickups[name] = pickup

            pickup.unknown_01 = read_uint8(df)
            assert pickup.unknown_01 == 0

            num_locations = read_uint8(df)

            pickup.unknown_02 = read_uint8(df)
            assert pickup.unknown_02 == 0

            for num_location in range(num_locations):

                location_name_1 = read_string(df)
                assert location_name_1 == name

                location_name_2 = read_string(df)
                pickup.locations[location_name_2] = read_stringlist(df)

                if num_location != num_locations-1:
                    zero = read_uint8(df)
                    assert zero == 0

        return pickups

    @staticmethod
    def write_pickups(df, pickups):
        """
        Write pickups to a file
        """
        write_uint8(df, len(pickups))
        for pickup in pickups.values():
            write_string(df, pickup.name)
            write_uint8(df, pickup.unknown_01)
            write_uint8(df, len(pickup.locations))
            write_uint8(df, pickup.unknown_02)
            for (idx, (loc_name, loc_pickups)) in enumerate(pickup.locations.items()):
                write_string(df, pickup.name)
                write_string(df, loc_name)
                write_stringlist(df, loc_pickups)
                if idx != len(pickup.locations)-1:
                    write_uint8(df, 0)

class Savegame(object):
    """
    Class to hold a SteamWorld Heist savegame.
    """

    # Hats!
    hats_base = [
            'youtube_hat', 'facebook_hat', 'twitter_hat', 'double_hat',
            'blue_fine_hat', 'shades', 'brownknitted', 'spinny',
            'goggle_hat', 'horns', 'lovely_hat', 'cavalier_cap',
            'cat_ears', 'javert_hat', 'rusty_hat', 'shiner_hat',
            'syd_vast', 'mutant_mudds', 'star_cowboy', 'goat_sim',
            'band_helmet', 'fedora', 'hankton_cap', 'intelligence_hat',
            'red_beret', 'heavy_chopper_hat', 'bowtie', 'goku_hair',
            'green_bro_cap', 'valkyrie', 'royal_wig', 'red_bro_cap',
            'royal_crown', 'bomb_deployer_hat', 'golem_cap', 'buzzer_hat',
            'ace_hat', 'mustache_hat', 'chopped_head', 'beetle_hat',
            'heavy_beetle_hat', 'beak_hat', 'catch_of_the_day', 'air_force_cap',
            'classic_ushanka', 'soft_cap', 'war_crown', 'blue_red_hat',
            'fez', 'funky_cap', 'blue_yellow_hat', 'crown',
            'green_ushanka', 'justice_circlet', 'snowboard_hat', 'cathat',
            'welder_cap', 'corshat', 'royalist_helmet', 'royalist_officer_hat',
            'royalist_blast_helmet', 'royalist_rider_helmet', 'pink_bandana', 'iron_cap',
            'armoured_tophat', 'medic_hat', 'army_helmet', 'bandit',
            'beret', 'boss_cap', 'bowler', 'brown_bowler',
            'cap', 'truckercap', 'captain', 'cowbot',
            'eggs_in_nest', 'fisherman', 'gunnar_hat', 'poof_hat',
            'goon_hat', 'pirate', 'pirate2', 'swab',
            'top', 'warm', 'tophatpurple', 'sailor_hat',
            'dragoon', 'fire_helmet', 'copperback_cap', 'caw-kaa',
        ]

    # More hats
    hats_dlc = {
            1: [
                'sauce_hat', 'prison_hat', 'pokercowboy', 'jones',
                'ash', 'jayne', 'layton', 'flower_crown',
                'shell_crown', 'petit_top_hat', 'cloud', 'turban',
                'wizzard', 'strawhat', 'dolores', 'hatoful',
                'flapper_band', 'marty_cap', 'jester', 'durkslag',
                'headphones', 'detectivecap',
                ],
            2: [
                'posthelm', 'sortinghat', 'bladerunner', 'first_crown',
                'five_hats', 'metropolis', 'miner_helm', 'spock',
                'squidberg', 'sw_helm'
                ],
        }

    def __init__(self):
        """
        Initialization.
        """
        pass

    def has_dlc(self, dlcnum):
        """
        Method to find out if this savegame has the given DLC enabled
        """
        if 'DLC/dlc{:02d}'.format(dlcnum).encode('utf-8') in self.dlc:
            return True
        else:
            return False

    def load(self, filename):
        """
        Loads ourself
        """

        # First load the file into a BytesIO object
        with open(filename, 'rb') as fileobj:
            df = io.BytesIO(fileobj.read())
        df.seek(0)

        # First there's just 0x01
        self.initial_01 = read_uint8(df)
        assert self.initial_01 == 1

        # Then a checksum
        self.checksum = read_uint32(df)

        # 0x03
        self.initial_03 = read_uint8(df)
        assert self.initial_03 == 3

        # Unknown byte of some sort; 0x14 and 0xf4 on completed games, 0x00 on not
        # Another seen value is 0xF6
        self.unknown_01 = read_uint8(df)

        # Six unknown bytes - I suspect this is an int (possibly either time-played
        # or turns-taken) followed by a short (or two bytes)
        self.unknown_02 = df.read(6)

        # 0x40: also seen: 0x41!  That 0x41 is only seen in a single of my savegames
        # so far.  Keeping the varname at 'initial_40' for now, though that's silly.
        self.initial_40 = read_uint8(df)
        #assert self.initial_40 == 0x40

        # Unknown byte of some sort; 0x14 and 0xf4 on completed games, 0x00 on not
        # Also seen: 0xE0
        self.unknown_03 = read_uint8(df)

        # Another six unknown bytes.  Probably related to either time-played or
        # turns-taken, at least partially
        self.unknown_04 = df.read(6)

        # Another unknown byte; 0x40 on nearly all my saves, but 0x00 on a
        # very earliest NG+ save.  Going to keep the var name but not do an
        # assert on it, I guess.
        self.initial_40_2 = read_uint8(df)
        #assert self.initial_40_2 == 0x40

        # Difficuly setting
        self.difficulty = read_string(df)

        # int, 2 for completed; maybe current location?
        self.current_loc = read_uint32(df)

        # usually 1
        self.usually_1 = read_uint32(df)

        # Unknown, 3 for completed, 0 otherwise
        self.unknown_05 = read_uint32(df)

        # Unknown, possibly related to number of different items seen
        self.unknown_06 = read_uint32(df)

        # Unknown, gets bigger as time passes
        self.unknown_07 = read_uint32(df)

        # Unknown, zero everywhere I've seen
        self.unknown_08 = read_uint16(df)

        # Unknown - the same everywhere though.
        self.unknown_09 = read_uint32(df)
        assert self.unknown_09 == 0x0262CFF8

        # DLC
        self.dlc = read_stringlist(df)

        # Another DLC list
        self.dlc2 = read_stringlist(df)

        # Unknown
        self.unknown_10 = read_uint16(df)

        # Some kind of character list, I guess?
        self.characters = Character.read_chars(df)

        # Unknown, is zero?  Bet it's another list.
        self.unknown_11 = read_uint8(df)
        assert self.unknown_11 == 0

        # Missions/whatever
        self.missions = Mission.read_missions(df)

        # More unknowns
        self.unknown_12 = read_uint8(df)
        self.unknown_13 = read_uint32(df)

        # Levels/whatever
        self.levels = Level.read_levels(df)

        # always 0x00?
        self.unknown_14 = read_uint8(df)
        assert self.unknown_14 == 0

        # Water!
        self.water = read_uint32(df)

        # No idea; the saves I have with an entry here are
        # all "treasure_scrappers"
        self.treasurelist = read_stringlist(df)

        # Unknown
        self.unknown_15 = read_uint8(df)

        # Last Item ID
        self.last_item_id = read_uint32(df)

        # Character equipment assigments.  The numbers match
        # the IDs which get assigned further down in the file.
        # There's a single byte (seemingly always 0x00), and
        # then five ints.  The first is the ID of the character,
        # and the next four are: weapon, accessory, accessory, hat.
        # Just leaving this as a tuple rather than tying it into
        # the Character class, though.
        self.equipment = []
        num_equips = read_uint8(df)
        for num in range(num_equips):
            self.equipment.append((
                read_uint8(df),
                read_uint32(df),
                read_uint32(df),
                read_uint32(df),
                read_uint32(df),
                read_uint32(df),
            ))

        # I think this might be related to the crew returning
        # to the ship after a mission; possibly just a list of
        # character IDs, in fact.
        self.return_list = read_uint32list(df)

        # Number of items in this list seems nearly always to be
        # the total number of unlocked characters, but in
        # 001-01-beginning.dat it's 1 rather than 2.  Not sure.
        self.unknown_char_list = read_uint32list(df)

        # Unknown, always zero
        self.unknown_17 = read_uint8(df)
        assert self.unknown_17 == 0

        # This, actually, is where I think the character IDs are
        # assigned; I should see if I can associate them back to
        # the equipment list items, earlier.
        self.char_id_order = []
        num_chars = read_uint8(df)
        self.char_by_id = {}
        for num in range(num_chars):
            idnum = read_uint32(df)
            name = read_string(df)
            self.char_id_order.append(name)
            self.characters[name].idnum = idnum
            self.char_by_id[idnum] = self.characters[name]

        # The list of unlocked characters
        self.unlocked_chars = read_stringlist(df)

        # Unknown, always zero
        self.unknown_18 = read_uint32(df)
        assert self.unknown_18 == 0

        # Unknown intlist
        self.unknown_19_list = read_uint32list(df)

        # Unknown, always zero
        self.unknown_19 = read_uint8(df)
        assert self.unknown_19 == 0

        # Hats!
        self.hats = Item.read_items(df)

        # Seen hats. Pretty weird, seems to be a repeat of the previous
        # hat structure but without the IDs (and in a different order).
        # I bet if you lose a hat to it being blown off, and don't pick
        # it up, it'll remain in this list even though it leaves the
        # inventory.  Not really sure why this would make a difference in-game
        # though.
        self.seen_hats = read_stringlist(df)

        # Unknown, always zero.  Maybe a "new hats" list like there is
        # for bank items, below?  Though new hats might just be included
        # in that list as well; I'm not sure if the IDs collide or not.
        self.unknown_20 = read_uint32(df)
        assert self.unknown_20 == 0

        # An odd intlist which I've only seen on my 'very beginning of the
        # game' savegame.  Has ten items, counting down from 0x0C to 0x03.
        # Weird.
        self.early_game_intlist = read_uint32list(df)

        # Unknown, always zero.
        self.unknown_21 = read_uint8(df)
        assert self.unknown_21 == 0

        # Bank items
        self.items = Item.read_items(df)

        # As with hats, a separate stringlist, seemingly just of items we've
        # seen.  Makes slightly more sense in this context, as this will be
        # a bigger list than what's in your bank (at least after a few
        # missions).  I suppose the hatlist may be different too, right?
        # What happens if your hat gets shot off and you don't manage to
        # pick it up afterwards?  Still, not really sure why the game even
        # needs a list of seen items; it doesn't seem to mater much to the
        # user...
        #self.seen_items = read_stringlist(df)
        # Also!  This is weird; on a few of my end-game savegames (after enabling
        # DLC), there's an errant 0x01 right after the uint8 specifying the
        # number of seen items.  Maybe this has to do with having seen DLC
        # items or something?  But if so, the number should be more than 1, yeah?
        # I dunno.  We're going to custom-process it for now.
        self.seen_items = []
        self.have_errant_seen_items_01 = False
        num_seen_items = read_uint8(df)
        if num_seen_items > 0:
            first_len = read_uint8(df)
            if first_len == 0x01:
                self.have_errant_seen_items_01 = True
                self.seen_items.append(read_string(df))
            else:
                self.seen_items.append(df.read(first_len))
            for num in range(num_seen_items-1):
                self.seen_items.append(read_string(df))

        # Inventory size!
        self.inventory_size = read_uint32(df)

        # Items marked 'new'
        self.new_items = read_uint32list(df)

        # Unknown, always zero.
        self.unknown_22 = read_uint8(df)
        assert self.unknown_22 == 0

        # Tips, presumably to do with character interactions
        self.tips = read_stringlist(df)

        # Unknown, always zero.
        self.unknown_23 = read_uint8(df)
        assert self.unknown_23 == 0

        # Some abilities
        self.abilities = read_stringlist(df)

        # Unknown, always zero.
        self.unknown_24 = read_uint8(df)
        assert self.unknown_24 == 0

        # Pickups; clearly related to loot somehow
        self.pickups = Pickup.read_pickups(df)

        # Unknown, always zero.
        self.unknown_25 = read_uint8(df)
        assert self.unknown_25 == 0

        ###
        ### Not actually going to bother decoding anything else in here.
        ### The only other thing I'd really care to figure out is how
        ### character abilities actually get unlocked (just setting the
        ### XP isn't enough, though the next time the character levels
        ### they'll receive all relevant abilities, so you can set the
        ### XP to 19999 and they'll get everything after the next
        ### mission).  Anyway, just from glancing through the file, it
        ### *looks* like that stuff might be spread out a bit towards
        ### the end of the file, and there's a lot to get through before
        ### you'd be able to get there.  (I think that the next big bit
        ### is the state of the current map - generally Piper's ship on
        ### my savegames, but would presumably be the actual level if
        ### you've quit mid-mission.  I don't really care enough to have
        ### to slog through figuring all that out.
        ###

        # Remaining data
        self.remaining_loc = df.tell()
        self.remaining = df.read()

        # Finally, at least for now (until we finish this up), verify
        # that generate_save() produces the exact same data as the original
        # file, before we make any changes.
        assert df.getvalue() == self.generate_save().getvalue()

    def generate_save(self):
        """
        Generate a BytesIO object which can then be saved out or processed further
        """

        # Create a BytesIO object to write into
        df = io.BytesIO()

        # First there's just 0x01
        write_uint8(df, self.initial_01)

        # Then a checksum.  This'll be wrong right now, but
        # we'll fix it later.
        write_uint32(df, self.checksum)

        # 0x03
        write_uint8(df, self.initial_03)

        # Unknown byte
        write_uint8(df, self.unknown_01)

        # Six unknown bytes
        df.write(self.unknown_02)

        # 0x40
        write_uint8(df, self.initial_40)

        # Unknown byte
        write_uint8(df, self.unknown_03)

        # Another six unknown bytes
        df.write(self.unknown_04)

        # Another 0x40
        write_uint8(df, self.initial_40_2)

        # Difficulty setting
        write_string(df, self.difficulty)

        # int, 2 for completed; maybe current location?
        write_uint32(df, self.current_loc)

        # usually 1
        write_uint32(df, self.usually_1)

        # Unknown, 3 for completed, 0 otherwise
        write_uint32(df, self.unknown_05)

        # Unknown, possibly related to number of different items seen
        write_uint32(df, self.unknown_06)

        # Unknown, gets bigger as time passes
        write_uint32(df, self.unknown_07)

        # Unknown, zero everywhere I've seen
        write_uint16(df, self.unknown_08)

        # Unknown - the same everywhere though.
        write_uint32(df, self.unknown_09)

        # DLC
        write_stringlist(df, self.dlc)

        # Another DLC list
        write_stringlist(df, self.dlc2)

        # Unknown
        write_uint16(df, self.unknown_10)

        # Some kind of character list, I guess?
        Character.write_chars(df, self.characters)

        # Unknown
        write_uint8(df, self.unknown_11)

        # Missions/whatever
        Mission.write_missions(df, self.missions)

        # Unknown
        write_uint8(df, self.unknown_12)
        write_uint32(df, self.unknown_13)

        # Levels/whatever
        Level.write_levels(df, self.levels)

        # always zero?
        write_uint8(df, self.unknown_14)

        # Water!
        write_uint32(df, self.water)

        # No idea
        write_stringlist(df, self.treasurelist)

        # Unknown
        write_uint8(df, self.unknown_15)

        # Last Item ID
        write_uint32(df, self.last_item_id)

        # Equipment
        write_uint8(df, len(self.equipment))
        for (b1, i1, i2, i3, i4, i5) in self.equipment:
            write_uint8(df, b1)
            write_uint32(df, i1)
            write_uint32(df, i2)
            write_uint32(df, i3)
            write_uint32(df, i4)
            write_uint32(df, i5)

        # returning-crew?
        write_uint32list(df, self.return_list)

        # No clue.
        write_uint32list(df, self.unknown_char_list)

        # Unknown
        write_uint8(df, self.unknown_17)

        # Character ID assignment
        write_uint8(df, len(self.char_id_order))
        for name in self.char_id_order:
            write_uint32(df, self.characters[name].idnum)
            write_string(df, name)

        # Unlocked characters
        write_stringlist(df, self.unlocked_chars)

        # Unknown
        write_uint32(df, self.unknown_18)
        write_uint32list(df, self.unknown_19_list)
        write_uint8(df, self.unknown_19)

        # Hats!
        Item.write_items(df, self.hats)

        # Seen hats?
        write_stringlist(df, self.seen_hats)

        # Unknown
        write_uint32(df, self.unknown_20)

        # early-game intlist?
        write_uint32list(df, self.early_game_intlist)

        # Unknown
        write_uint8(df, self.unknown_21)

        # Bank items
        Item.write_items(df, self.items)

        # Seen items
        #write_stringlist(df, self.seen_items)
        write_uint8(df, len(self.seen_items))
        if self.have_errant_seen_items_01:
            write_uint8(df, 1)
        for item in self.seen_items:
            write_string(df, item)

        # Inventory size
        write_uint32(df, self.inventory_size)

        # new items
        write_uint32list(df, self.new_items)

        # Unknown
        write_uint8(df, self.unknown_22)

        # Tips
        write_stringlist(df, self.tips)

        # Unknown
        write_uint8(df, self.unknown_23)

        # Abilities?
        write_stringlist(df, self.abilities)

        # Unknown
        write_uint8(df, self.unknown_24)

        # Pickups
        Pickup.write_pickups(df, self.pickups)

        # Unknown
        write_uint8(df, self.unknown_25)

        # Remaining data
        df.write(self.remaining)

        # Now fix the checksum
        df.seek(1)
        new_checksum = binascii.crc32(df.getvalue()[5:])
        write_uint32(df, new_checksum)

        # Return
        df.seek(0)
        return df

    def save(self, filename):
        """
        Write out ourself to a file
        """

        savedata = self.generate_save()
        with open(filename, 'wb') as fileobj:
            fileobj.write(savedata.getvalue())

    def add_item(self, itemname):
        """
        Adds a new item to our item list.
        """
        self.last_item_id += 1
        self.items[self.last_item_id] = Item(name=itemname, idnum=self.last_item_id)
        if itemname not in self.seen_items:
            self.seen_items.append(itemname)

    def add_hat(self, hatname):
        """
        Adds a new hat to our hat list.
        """
        self.last_item_id += 1
        self.hats[self.last_item_id] = Item(name=hatname, idnum=self.last_item_id)
        if hatname not in self.seen_hats:
            self.seen_hats.append(hatname)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
            description='View/Edit SteamWorld Heist Savegames',
        )

    parser.add_argument('input',
        type=str,
        metavar='FILENAME',
        nargs=1,
        help='Input filename')

    group = parser.add_mutually_exclusive_group()

    group.add_argument('-l', '--list',
        action='store_true',
        help='Just show information about the savegame')

    group.add_argument('-c', '--check',
        action='store_true',
        help='Just check that we can load the file and can produce a 100%%-accurate replica')

    group.add_argument('-o', '--output',
        type=str,
        help='Output filename (required if making changes)')

    parser.add_argument('-e', '--experience',
        action='store_true',
        help='Set all unlocked character XP to 19999')

    parser.add_argument('-w', '--water',
        type=int,
        help='Set Water value (money)')

    parser.add_argument('-s', '--size',
        type=int,
        help='Set new total inventory size')

    parser.add_argument('-i', '--inventory',
        action='store_true',
        help="""Add a frankly ludicrous number of powerful items to
            inventory (will add appropriate inventory space automatically
            unless --size is specified, in which case --size is used)""")

    parser.add_argument('-a', '--additem',
        type=str,
        action='append',
        metavar='item[,item,...]',
        help="""Add a specific item to the inventory.  Can specify this
            option multiple times, and/or specify a list of items 
            separated by commas.  (Will increase inventory size automatically
            if required.)""")

    parser.add_argument('-t', '--hats',
        action='store_true',
        dest='hats',
        help='Add all hats to the savegame.')

    parser.add_argument('-v', '--verbose',
        action='count',
        help="""Show extra information during list.  Specify more than once
            to also show a hexdump of data at the point we stopped parsing.""")

    args = parser.parse_args()

    if (args.list or args.check) and (args.experience or args.water or
            args.size or args.inventory or args.additem or args.hats):
        parser.error('--list and --check cannot be used with any of the editing flags')

    if args.output and not args.experience and not args.water and \
            not args.size and not args.inventory and not args.additem and \
            not args.hats:
        parser.error('Specify a modification to make if not using --list')

    # Load the savegame
    sg = Savegame()
    sg.load(args.input[0])

    # Do what's required
    if args.list:

        # Displaying character names
        if args.verbose:
            print('Total seen characters:')
            for char in sg.characters.keys():
                print('  * {}'.format(char.decode('utf-8')))
            print('')

        # Displaying player characters' current XP levels
        print('Character XP levels:')
        for charname in sg.unlocked_chars:
            if charname in sg.characters:
                char = sg.characters[charname]
                if b'upgrades' in char.attributes:
                    print('  * {}: {}'.format(charname.decode('utf-8'), char.attributes[b'upgrades']))
                else:
                    # NG+ characters don't seem to start out with an 'upgrades' attribute
                    print('  * {}: no XP level set'.format(charname.decode('utf-8')))
        print('')

        # Displaying mission names
        if args.verbose:
            print('Mission names:')
            for mission in sg.missions.keys():
                print('  * {}'.format(mission.decode('utf-8')))
            print('')

        # Displaying level names
        if args.verbose:
            print('Level names:')
            for level in sg.levels.keys():
                print('  * {}'.format(level.decode('utf-8')))
            print('')

        # Water!
        print('Water: {}'.format(sg.water))
        print('')

        # hat information!
        if args.verbose:
            print('Current hat inventory:')
            if len(sg.hats) > 0:
                for hat in sg.hats.values():
                    print('  * {}'.format(hat.name.decode('utf-8')))
            else:
                print('  (none)')
            print('')
            print('Total list of seen hats:')
            if len(sg.seen_hats) > 0:
                for hat in sg.seen_hats:
                    print('  * {}'.format(hat.decode('utf-8')))
            else:
                print('  (none)')
            print('')

        # item information!
        print('Total inventory size: {}'.format(sg.inventory_size))
        print('Current item inventory:')
        if len(sg.items) > 0:
            for item in sg.items.values():
                print('  * {}'.format(item.name.decode('utf-8')))
        else:
            print('  (none)')
        print('')
        if args.verbose:
            print('Total list of seen items:')
            if len(sg.seen_items) > 0:
                for item in sg.seen_items:
                    print('  * {}'.format(item.decode('utf-8')))
            else:
                print('  (none)')
            print('')

        # Item assignments
        print('Item assignments:')
        for (b, i1, i2, i3, i4, i5) in sg.equipment:
            print('  * {}'.format(sg.char_by_id[i1].name.decode('utf-8')))
            for (item_id, label) in [
                    (i2, 'Weapon'),
                    (i3, 'Accessory 1'),
                    (i4, 'Accessory 2'),
                    ]:
                if item_id in sg.items:
                    print('     {}: {}'.format(label, sg.items[item_id].name.decode('utf-8')))
            if i5 in sg.hats:
                print('     Hat: {}'.format(sg.hats[i5].name.decode('utf-8')))
            print('')

        # New items
        if args.verbose:
            print('Items marked as "new":')
            if len(sg.new_items) > 0:
                for idnum in sg.new_items:
                    if idnum in sg.items:
                        print('  * New item: {}'.format(sg.items[idnum].name.decode('utf-8')))
                    else:
                        print('  * Unknown new item ID: {}'.format(idnum))
            else:
                print('  (none)')
            print('')

    elif args.output:

        if args.experience:
            # Set all active characters' XP to 19999
            # TODO: Figure out how abilities actually unlock; as it is,
            # setting the XP doesn't actually grant the abilities the
            # char would be entitled to, though once the character
            # levels up, they seem to get the abilities (so setting it
            # to 19999 lets them level up and acquire abilities on the
            # very next mission).  I think that may just be further on
            # in the file; I seem to recall seeing it.
            for charname in sg.unlocked_chars:
                if charname in sg.characters:
                    char = sg.characters[charname]
                    if b'upgrades' in char.attributes:
                        if char.attributes[b'upgrades'] < 19999:
                            char.attributes[b'upgrades'] = 19999
                            print('Set {} XP to 19999'.format(charname.decode('utf-8')))
                        else:
                            print('{} is already at {} XP, skipping'.format(
                                charname.decode('utf-8'), char.attributes[b'upgrades']))
                    else:
                        # NG+ characters don't seem to start out with an 'upgrades' attribute
                        char.attributes[b'upgrades'] = 19999
                        print('Set {} XP to 19999 (from 0 XP previously)'.format(charname.decode('utf-8')))

        if args.water:
            # Set water value
            sg.water = args.water
            print('Set water value to {}'.format(args.water))

        if args.size:
            # Set inventory size
            sg.inventory_size = args.size
            print('Set inventory size to {}'.format(args.size))
            
        if args.inventory:

            # Pistols
            itemlist = [
                    b'handgun_09', b'handgun_09', b'handgun_rare_09', b'handgun_rare_09',
                ]

            # Assault
            if self.has_dlc(1):
                itemlist += [
                        b'smg_09', b'smg_09', b'smg_09', b'shotgun_09',
                        b'smg_rare_09', b'smg_rare_09', b'smg_rare_09', b'shotgun_09',
                    ]
            else:
                itemlist += [
                        b'shotgun_09', b'shotgun_09', b'smg_dlc01', b'smg_dlc01',
                        b'smg_09', b'smg_09', b'smg_rare_09', b'smg_rare_09',
                    ]

            # Sniper
            itemlist += [
                    b'scoped_09', b'scoped_09', b'scoped_09', b'sniper_09',
                    b'sniper_rare_09', b'sniper_rare_09', b'sniper_rare_09', b'sniper_09',
                ]

            # Heavy
            if self.has_dlc(1):
                itemlist += [
                        b'rpg_09', b'rpg_09', b'rpg_rare_09', b'rpg_rare_09',
                        b'lobber_09', b'lobber_09', b'minigun_rare_09', b'minigun_rare_09',
                    ]
            else:
                itemlist += [
                        b'rpg_09', b'rpg_09', b'rpg_rare_09', b'rpg_rare_09',
                        b'lobber_09', b'minigun_rare_09', b'rpg_dlc01', b'rpg_dlc01',
                    ]

            itemlist += [

                    # Mobility
                    b'jetpack', b'jetpack', b'jetpack', b'jetpack',
                    b'speed_boots_3', b'speed_boots_3', b'speed_boots_3', b'speed_boots_3',
                    b'dancing_shoes', b'dancing_shoes', b'overheat', b'overheat',

                    # Mobility -> Melee
                    b'energy_surge_generator', b'energy_surge_generator', b'dynamo', b'dynamo',

                    # Melee
                    b'judo_gloves', b'judo_gloves', b'electrified_knuckles', b'electrified_knuckles',

                    # Damage
                    b'ammo_radioactive', b'ammo_radioactive', b'ammo_radioactive', b'ammo_radioactive',
                    b'ammo_radioactive', b'ammo_radioactive', b'ammo_radioactive', b'ammo_radioactive',
                    b'ammo_critical_superior', b'ammo_critical_superior', b'ammo_critical_superior', b'ammo_critical_superior',
                ]

            # Damage (continued)
            if self.has_dlc(1):
                itemlist += [
                        b'ammo_berserker', b'ammo_berserker', b'ammo_berserker', b'ammo_berserker',
                    ]
            
            itemlist += [

                    # Damage (continued)
                    b'goggles', b'goggles', b'goggles', b'goggles',

                    # Healing
                    b'quick_patch', b'quick_patch', b'quick_patch', b'quick_patch',

                    # Grenades
                    b'plasma_grenade', b'plasma_grenade', b'plasma_grenade', b'plasma_grenade',
                    b'stun_grenade', b'stun_grenade', b'stun_grenade', b'oil_grenade',
                    b'freeze_bomb', b'freeze_bomb', b'freeze_bomb', b'oil_grenade',

                    # Sidearms
                    b'vectron_sidearm', b'vectron_sidearm', b'stun_gun', b'stun_gun',

                    # Armor
                    b'exoskeleton', b'exoskeleton', b'exoskeleton', b'exoskeleton',
                    b'armor_3', b'armor_3', b'armor_swift', b'armor_swift',
                ]

            # Armor (continued)
            if self.has_dlc(1):
                itemlist += [
                        b'armor_retaliating', b'armor_retaliating', b'armor_retaliating', b'armor_retaliating',
                    ]

            # Armor (continued)
            itemlist += [
                    b'steroid_coal', b'steroid_coal', b'steroid_coal', b'steroid_coal',
                ]

            # Taunt Horn (can't imagine you'd want all four of these, but whatever)
            if self.has_dlc(1):
                itemlist += [
                        b'taunt_horn', b'taunt_horn', b'taunt_horn', b'taunt_horn',
                    ]

            if not args.size:
                sg.inventory_size += len(itemlist)
            for itemstr in itemlist:
                sg.add_item(itemstr)
            if args.size:
                print('Added {} items to inventory'.format(len(itemlist)))
            else:
                print('Added {} items to inventory (and added that much inventory space)'.format(len(itemlist)))

        # Add specified items
        if args.additem:
            full_item_list = []
            for item_list in args.additem:
                individual_items = item_list.split(',')
                for item in individual_items:
                    full_item_list.append(item)
            for item in full_item_list:
                sg.add_item(item.encode('utf-8'))
                print('Added item: {}'.format(item))

        # Sanity check on inventory size
        if sg.inventory_size < len(sg.items):
            print('Increasing inventory size to {} to accomodate items (previously {})'.format(
                len(sg.items), sg.inventory_size))
            sg.inventory_size = len(sg.items)

        # Add hats
        if args.hats:
            hatlist = sg.hats_base
            for dlcnum in [1, 2]:
                if sg.has_dlc(dlcnum):
                    hatlist += sg.hats_dlc[dlcnum]
            hats_added = 0
            for hatname in hatlist:
                encoded = hatname.encode('utf-8')
                if encoded not in sg.seen_hats:
                    sg.add_hat(encoded)
                    hats_added += 1
            print('Added {} hats ({} already present)'.format(hats_added, len(hatlist)-hats_added))

        sg.save(args.output)
        print('')
        print('Saved edited savegame to {}'.format(args.output))

    if args.verbose and args.verbose > 1:
        # Print the next bunch of data we haven't parsed yet.
        per_line = 32
        lines = 10
        printable_chars = b'0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ '
        for line in range(lines):
            start = line*per_line
            sys.stdout.write('0x{:08X}  '.format(sg.remaining_loc+start))
            for (idx, byte) in enumerate(sg.remaining[start:start+per_line]):
                sys.stdout.write('{:02X}'.format(byte))
                sys.stdout.write(' ')
                if idx % 4 == 3:
                    sys.stdout.write(' ')
            sys.stdout.write('| ')
            for byte in sg.remaining[start:start+per_line]:
                if byte in printable_chars:
                    sys.stdout.write(chr(byte))
                else:
                    sys.stdout.write('.')
            sys.stdout.write("\n")
