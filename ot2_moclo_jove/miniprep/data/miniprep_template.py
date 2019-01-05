from opentrons import robot, instruments, labware, modules

available_deck_slots = ['1', '2', '3', '4', '5', '6', '8', '9']

tip_racks = [labware.load('tiprack-200ul', available_deck_slots.pop(), 'tiprack-200ul') for x in range(0, 4)]

p300 = instruments.P300_Multi(mount='left', tip_racks=tip_racks)

mag = modules.load("magdeck", "10", share=True)
samples = labware.load('96-deep-well', "10", 'samples', share=True)
dest_plate = labware.load("96-PCR-tall", "11", "destination plate")
buffers = labware.load("trough-12row", "7", "buffers")
etr_mag = [buffers.wells(0), buffers.wells(1)]
etr = [buffers.wells(2), buffers.wells(3)]
vhb = [buffers.wells(4), buffers.wells(5), buffers.wells(6), buffers.wells(7)]
spm = [buffers.wells(8), buffers.wells(9)]
eb = buffers.wells(10)

#Add 500 킠 ETR and 20 킠 Mag-Bind
p300.transfer(520, etr_mag.bottom(0.5), 
#Wait 5 min
#Magnetize and discard supernatant
#Demagnetize and add 500 킠 ETR
#Magnetize and discard supernatant
#Demagnetize and add 700 킠 VHB
#Magnetize and discard supernatant
#Demagnetize and add 700 킠 VHB
#Magnetize and discard supernatant
#Demagnetize and aAdd 700 킠 SPM
#Magnetize and discard supernatant
#Wait 1 min
#Discard last bit of supernatant
#Wait 9 min
#Demagnetize and add 50-100 킠 Elution Buffer (might be able to add less)
#Magnetize and remove and save supernatant (which contains dna)



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


