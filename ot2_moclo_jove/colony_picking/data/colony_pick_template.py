# This is the template protocol for colony picking. culture_blocks_dict (see below) will be hardcoded 
# in at the top of this file by the colony_pick_generator.py script to create the final protocol file.

# TODO: Automatically break up into multiple parts if too many colonies to pick

# The structure of the dictionary pasted into the top of this file is below. Each culture block is represented 
# by a list of lists. Each entry contains the name of the plasmid ('name'), the agar plate it came from 
# ('source'), and the x y position in mm of the colony it came from ('x' and 'y').
# For example...
# culture_blocks_dict = {
# 	'culture_block_0': [
# 		[
# 			{'name': 'plasmid_name_1', 'source': 'agar_plate_0', 'x': 12.123, 'y': 14.13}, 
# 			{'name': 'plasmid_name_1', 'source': 'agar_plate_0', 'x': 15.12, 'y': 12.0}
# 		],
# 		[
# 			{'name': 'plasmid_name_13', 'source': 'agar_plate_3', 'x': 14.123, 'y': 17.13},
# 			{'name': 'plasmid_name_14', 'source': 'agar_plate_3', 'x': 10.1, 'y': 20.01}
# 		]
# 	],
# 	'culture_block_1': [
# 		[
# 			{'name': 'plasmid_name_14', 'source': 'agar_plate_3', 'x': 12.3, 'y': 15.13}, 
# 			{'name': 'plasmid_name_15', 'source': 'agar_plate_3', 'x': 15.12, 'y': 12.0}
# 		],
# 		[
# 			{'name': 'plasmid_name_17', 'source': 'agar_plate_4', 'x': 17.123, 'y': 11.13},
# 			{'name': 'plasmid_name_18', 'source': 'agar_plate_4', 'x': 20.1, 'y': 15.01}
# 		]
# 	],
# }

from opentrons import robot, instruments, labware
from opentrons.util.vector import Vector

# How far from the calibration point to move the pipette down when picking colonies.
PLATE_DEPTH = -7

available_deck_slots = ['11', '10', '9', '8', '7', '6', '5', '4', '3', '2', '1']

tip_rack = [labware.load('tiprack-10ul', available_deck_slots.pop(), 'tiprack-10ul')]

p = instruments.P10_Single(mount='right', tip_racks=tip_rack)

culture_block = labware.load('96-deep-well', available_deck_slots.pop(), 'culture_block')

source_plate_names = []
for block_name, block_map in culture_blocks_dict.items():
	for row in block_map:
		for element in row:
			source_name = element['source']
			if not source_name in source_plate_names:
				source_plate_names.append(source_name)

source_plates = {}
for name in source_plate_names:
	source_plates[name] = labware.load('point-for-colony-picking', available_deck_slots.pop(), name)

i = 0
for block_name, block_map in culture_blocks_dict.items():
	for row in block_map:
		for colony in row:
			p.pick_up_tip()
			# This aspirate ensures that the OT2 app realizes we are actually using this plate (so that it will 
			# tell the user to calibrate for it).
			p.aspirate(10, source_plates[colony['source']].wells(0))
			robot.move_to((source_plates[colony['source']], Vector([colony['x'], colony['y'], PLATE_DEPTH])), p)
			p.dispense(10, culture_block.wells(i))
			p.aspirate(10)
			p.dispense(10)
			p.drop_tip()

			i += 1