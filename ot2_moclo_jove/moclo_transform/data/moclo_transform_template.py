import math

from opentrons import robot, instruments, labware, modules

# Up to 48 rxns per run (4 spots on agar per rxn)
# Multichannel p300, single channel p10
# This protocol is optimized for maximum walkaway time

import random
test_part_names = [str(x) for x in range(0, 288)]
test_plasmid_names = [str(x) for x in range(0, 48)]
combinations_to_make = []
for i in test_plasmid_names:
	combination = {}
	combination["name"] = i
	combination["parts"] = [str(random.randint(0, 191)) for x in range(0, 5)]
	combinations_to_make.append(combination)

def gen_part_plate(offset):
	plate_map = []
	for i in range(0, 8):
		plate_map.append([str(x) for x in range(i*12 + offset, i*12 + offset + 12)])
	return plate_map

dna_plate_map_dict = {}
dna_plate_map_dict["plate_0"] = gen_part_plate(0)
dna_plate_map_dict["plate_1"] = gen_part_plate(96)

combinations_to_make = [{"name": "final plasmid 1", "parts": ["vector a", "insert 1", "another insert"]}]
dna_plate_map_dict = {"dna plate 0": [["vector a", "insert 1", "another insert"]]}

num_rxns = len(combinations_to_make)
num_plates = math.ceil(num_rxns/24)

# Load in 96-well PCR plate (96-PCR-flat) on temp deck for moclos, transformation, and outgrowth.
temp_deck = modules.load('tempdeck', '10')
reaction_plate = labware.load('96-PCR-flat', '10', share=True)

available_deck_slots = ['11', '8', '7', '5', '4', '2', '1']

# Load in 1 10ul tiprack and 2 300ul tipracks
tr_10 = [labware.load('tiprack-10ul', '3'), labware.load('tiprack-10ul', '6')]
tr_300 = []
for i in range(0, 1):
	tr_300.append(labware.load('tiprack-200ul', '9'))

# Load in pipettes
p10_single = instruments.P10_Single(mount='right', tip_racks=tr_10)
p300_multi = instruments.P300_Multi(mount='left', tip_racks=tr_300)

# Load in reagent tubes on cold block (PCR-strip-tall)
reagents = labware.load('PCR-strip-tall', available_deck_slots.pop(), 'Reagent plate')
ligase = reagents.wells(0)
restriction_enzyme = reagents.wells(1)
buffer = reagents.wells(2)

# Load in water, LB, and wash trough (trough-12row)
trough = labware.load('trough-12row', available_deck_slots.pop(), 'Reagent trough')
water = trough.wells(0)
lb = trough.wells(1)
wash_0 = trough.wells(2)
wash_1 = trough.wells(3)

# Load in up to 2 DNA plates (96-PCR-flat)
dna_plate_dict = {}
for plate_name in dna_plate_map_dict.keys():
	dna_plate_dict[plate_name] = labware.load('96-PCR-flat', available_deck_slots.pop(), plate_name)

# Load in comp cell plate (96-PCR-flat)
comp_cells = labware.load('96-flat', available_deck_slots.pop(), 'Competent cells')

# Load in up to 2 agar plates, same antibiotic for all plasmids is assumed (e-gelgol)
agar_plates = []
for i in range(0, num_plates):
	agar_plates.append(labware.load('e-gelgol', available_deck_slots.pop(), 'Agar plate {0}'.format(i)))

# Add water, buffer, restriction enzyme, ligase, and buffer to 2x master mix.
# Add extra space for dead volume.
num_mm_wells = math.ceil(num_rxns * 10 / 190.0)
mm_to_make = 10 * num_rxns + 10 * num_mm_wells
mm_wells = []
p10_single.pick_up_tip()
well_in_plate = 95
while mm_to_make > 0:
	if mm_to_make > 200:
		vol = 200
		mm_to_make -= 200
	else:
		vol = mm_to_make
		mm_to_make = 0
	mm_well = reaction_plate.wells(well_in_plate)
	well_in_plate -= 1
	mm_wells.append(mm_well)
	p10_single.transfer(0.65*vol, water.bottom(), mm_well.bottom(), new_tip='never')
	p10_single.transfer(vol/5.0, buffer.bottom(), mm_well.bottom(), mix_after=(2, 10), new_tip='never')
	p10_single.transfer(vol/20.0, ligase.bottom(), mm_well.bottom(), mix_after=(2, 10), new_tip='never')
	p10_single.transfer(vol/10.0, restriction_enzyme.bottom(), mm_well.bottom(), mix_after=(5, 10), new_tip='never')
p10_single.drop_tip()

# Add master mix to each rxn
p10_single.pick_up_tip()
mm_well = 0
for i in range(0, num_rxns):
	mm_well = mm_wells[i // 19]
	p10_single.transfer(10, mm_well.bottom(), reaction_plate.wells(i).bottom(), new_tip='never')
p10_single.drop_tip()

def find_dna(name, dna_plate_map_dict, dna_plate_dict):
	"""Return a well containing the named DNA."""
	for plate_name, plate_map in dna_plate_map_dict.items():
		for i, row in enumerate(plate_map):
			for j, dna_name in enumerate(row):
				if dna_name == name:
					well_num = 8 * j + i
					return(dna_plate_dict[plate_name].wells(well_num))
	raise ValueError("Could not find dna piece named \"{0}\"".format(name))

def find_combination(name, combinations_to_make):
	"""Return a well containing the named combination."""
	for i, combination in enumerate(combinations_to_make):
		if combination["name"] == name:
			return reaction_plate.wells(i)
	raise ValueError("Could not find combination \"{0}\".".format(name))

combinations_by_part = {}
for i in combinations_to_make:
	name = i["name"]
	for j in i["parts"]:
		if j in combinations_by_part.keys():
			combinations_by_part[j].append(name)
		else:
			combinations_by_part[j] = [name]

for part, combinations in combinations_by_part.items():
	part_well = find_dna(part, dna_plate_map_dict, dna_plate_dict).bottom()
	combination_wells = [find_combination(x, combinations_to_make).bottom() for x in combinations]
	p10_single.distribute(2, part_well, combination_wells)

for i in combinations_to_make:
	num_parts = len(i["parts"])
	if num_parts < 5:
		water_to_add = 10 - 2 * num_parts
	else:
		water_to_add = 0
	well = find_combination(i["name"], combinations_to_make)
	p10_single.transfer(water_to_add, water.bottom(), well.bottom(), mix_after=(4, 10))

# Incubate rxns (moclo), periodically adding more water.
#temp_deck.set_temperature(37)
#p10_single.delay(minutes=120)
#temp_deck.set_temperature(50)
#p10_single.delay(minutes=5)
#temp_deck.set_temperature(80)
#p10_single.delay(minutes=10)
#temp_deck.set_temperature(4)

# Discard majority of rxn volume using multichannel.
num_cols = math.ceil(num_rxns/8.0)
p300_multi.pick_up_tip()
for i in range(0, num_cols):
	# Split up if too many rxns for one tip
	if i % 15 == 0 and not i == 0:
		p300_multi.dispense(300, robot.fixed_trash)
	p300_multi.aspirate(15, reaction_plate.wells(i*8).bottom())
	p300_multi.air_gap(5)
p300_multi.drop_tip()

# Add comp cells.
p300_multi.pick_up_tip()
for i in range(0, num_cols):
	p300_multi.aspirate(50, comp_cells.wells(i*8).bottom())

for i in range(0, num_cols):
	p300_multi.dispense(50, reaction_plate.wells(i*8).bottom())
p300_multi.drop_tip()

# Incubate at 4C, then heat shock.
#p10_single.delay(minutes=30)
#temp_deck.set_temperature(42)
#p10_single.delay(minutes=1)
#temp_deck.set_temperature(4)
#p10_single.delay(minutes=5)

# Add lb.
p300_multi.pick_up_tip()
for i in range(0, num_cols):
	p300_multi.transfer(150, lb.bottom(), reaction_plate.wells(i*8).bottom(), mix_after=(2, 150), new_tip='never')
	p300_multi.mix(2, 300, wash_0.bottom())
	p300_multi.mix(2, 300, wash_1.bottom())
p300_multi.drop_tip()

# Grow for 1 hr, adding water/mixing if necessary.
#temp_deck.set_temperature(37)
#p10_single.delay(minutes=60)

def spread_culture(source, dest, lb, dilute_after=True):
	p300_multi.mix(2, 150, source)
	p300_multi.aspirate(30, source.bottom())
	p300_multi.dispense(30, dest.top())
	p300_multi.dispense(0, dest.bottom(-1))
	if dilute_after:
		p300_multi.transfer(100, source, robot.fixed_trash, new_tip='never')
		p300_multi.transfer(100, lb, source, new_tip='never')

# Dilute and plate.
for i in range(0, num_cols):
	agar_plate = agar_plates[i // 3]
	agar_well_num = (i % 3) * 8 * 3
	p300_multi.pick_up_tip()
	source = reaction_plate.wells(i*8)
	spread_culture(source, agar_plate.wells(agar_well_num), lb)
	spread_culture(source, agar_plate.wells(agar_well_num + 8), lb)
	spread_culture(source, agar_plate.wells(agar_well_num + 16), lb)
	spread_culture(source, agar_plate.wells(agar_well_num + 24), lb, dilute_after=False)
	p300_multi.drop_tip()

