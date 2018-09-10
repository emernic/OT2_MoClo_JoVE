from opentrons import robot, instruments, labware

###############################################################################################
# TODO: Put in the actual protocol for moclo. This is just copy pasted from colony picking as 
# an example.
###############################################################################################

available_deck_slots = ['11', '10', '9', '8', '7', '6', '5', '4', '3', '2', '1']

tip_rack = [labware.load('tiprack-10ul', available_deck_slots.pop(), 'tiprack-10ul')]

p = instruments.P10_Single(mount='left', tip_racks=tip_rack)

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