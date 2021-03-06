import time
import math

from opentrons import robot, instruments, labware, modules

COLD_BLOCK = '96-PCR-tall-cold-block'
try:
	labware.create(
		COLD_BLOCK,
		grid=(12, 8),
		spacing=(9, 9),
		diameter=5,
		depth=15.4,
		volume=200)
except:
	print("Using existing labware definition for {0}".format(COLD_BLOCK))

# Up to 48 rxns per run (4 spots on agar per rxn)
# Multichannel p300, single channel p10
# This protocol is optimized for maximum walkaway time

num_rxns = len(combinations_to_make)
num_plates = math.ceil(num_rxns/24)

# Load in 96-well PCR plate (96-PCR-flat) on temp deck for moclos, transformation, and outgrowth.
temp_deck = modules.load('tempdeck', '10')
reaction_plate = labware.load('96-PCR-tall', '10', share=True)

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
liquid_waste = trough.wells(4)

# Load in up to 2 DNA plates (96-PCR-flat)
dna_plate_dict = {}
for plate_name in dna_plate_map_dict.keys():
	dna_plate_dict[plate_name] = labware.load('96-PCR-tall', available_deck_slots.pop(), plate_name)

# Load in comp cell plate (96-PCR-flat)
comp_cells = labware.load(COLD_BLOCK, available_deck_slots.pop(), 'Competent cells')

# Load in up to 2 agar plates, same antibiotic for all plasmids is assumed (e-gelgol)
agar_plates = []
for i in range(0, num_plates):
	agar_plates.append(labware.load('e-gelgol', available_deck_slots.pop(), 'Agar plate {0}'.format(i)))

temp_deck.set_temperature(10)

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
	water_to_transfer = 0.65*vol
	# Transfer large volumes first to avoid dead volume.
	while water_to_transfer > 0:
		if water_to_transfer > 10:
			p10_single.transfer(10, water.bottom(), mm_well.bottom(0.5), new_tip='never')
			water_to_transfer -= 10
		else:
			p10_single.transfer(water_to_transfer, water.bottom(), mm_well.bottom(0.5), new_tip='never')
			water_to_transfer = 0
	p10_single.transfer(vol/5.0, buffer.bottom(), mm_well.bottom(0.5), new_tip='never')
	p10_single.mix(2, 10, mm_well.bottom(0.5))
	p10_single.transfer(vol/20.0, ligase.bottom(), mm_well.bottom(0.5), new_tip='never')
	p10_single.mix(2, 10, mm_well.bottom(0.5))
	p10_single.transfer(vol/10.0, restriction_enzyme.bottom(), mm_well.bottom(0.5), new_tip='never')
	p10_single.mix(5, 10, mm_well.bottom(0.5))
p10_single.drop_tip()

# Add master mix to each rxn
p10_single.pick_up_tip()
mm_well = 0
for i in range(0, num_rxns):
	mm_well = mm_wells[i // 19]
	p10_single.transfer(10, mm_well.bottom(0.5), reaction_plate.wells(i).bottom(0.5), new_tip='never')
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
	part_well = find_dna(part, dna_plate_map_dict, dna_plate_dict)
	combination_wells = [find_combination(x, combinations_to_make) for x in combinations]
	p10_single.pick_up_tip()
	while combination_wells:
		if len(combination_wells) > 5:
			current_wells = combination_wells[0:5]
			combination_wells = combination_wells[5:]
		else:
			current_wells = combination_wells
			combination_wells = []
		p10_single.aspirate(2 * len(current_wells), part_well.bottom(0.5))
		for i in current_wells:
			p10_single.dispense(2, i.bottom(0.5))
		if combination_wells:
			p10_single.mix(2, 10, wash_0.bottom(0.5))
			p10_single.blow_out()
			p10_single.mix(2, 10, wash_1.bottom(0.5))
			p10_single.blow_out()
	p10_single.drop_tip()

num_cols = math.ceil(num_rxns/8.0)
p10_single.pick_up_tip()
for i in combinations_to_make:
	num_parts = len(i["parts"])
	# Start off with extra 2 ul of water for evaporation.
	water_to_add = 12 - 2 * num_parts
	if water_to_add < 0:
		water_to_add = 0
	well = find_combination(i["name"], combinations_to_make)
	p10_single.transfer(water_to_add, water.bottom(), well.bottom(0.5), new_tip='never')
	p10_single.mix(4, 10, well.bottom(0.5))
	p10_single.mix(2, 10, wash_0.bottom(0.5))
	p10_single.blow_out()
	p10_single.mix(2, 10, wash_1.bottom(0.5))
	p10_single.blow_out()
p10_single.drop_tip()

# Incubate rxns for 2 hr (moclo), adding 4 ul of water halfway through.
start_time = time.time()
temp_deck.set_temperature(37)
p10_single.delay(minutes=60)
p10_single.pick_up_tip()
for i in combinations_to_make:
	num_parts = len(i["parts"])
	# Add an extra 4 ul of water for evaporation.
	water_to_add = 4
	well = find_combination(i["name"], combinations_to_make)
	p10_single.transfer(water_to_add, water.bottom(), well.bottom(0.5), new_tip='never')
	p10_single.mix(4, 10, well.bottom(0.5))
	p10_single.mix(2, 10, wash_0.bottom(0.5))
	p10_single.blow_out()
	p10_single.mix(2, 10, wash_1.bottom(0.5))
	p10_single.blow_out()
p10_single.drop_tip()
time_elapsed = time.time() - start_time
p10_single.delay(seconds=(120*60 - time_elapsed))
temp_deck.set_temperature(4)

# Add comp cells.
p300_multi.pick_up_tip()
for i in range(0, num_cols):
	# Using letters for rows of custom container to maintain backwards compatibility.
	p300_multi.aspirate(20, comp_cells.wells('A' + str(i + 1)).bottom(0.5))

for i in range(0, num_cols):
	p300_multi.dispense(20, reaction_plate.wells(48 + i*8).bottom(0.5))
p300_multi.drop_tip()

# Add 2 ul of rxns to comp cells
p10_single.pick_up_tip()
for i in range(0, num_rxns):
	p10_single.transfer(2, reaction_plate.wells(i).bottom(0.5), reaction_plate.wells(48 + i).bottom(0.5), new_tip='never')
	p10_single.mix(4, 10, reaction_plate.wells(48 + i).bottom(0.5))
	p10_single.mix(2, 10, wash_0.bottom(0.5))
	p10_single.blow_out()
	p10_single.mix(2, 10, wash_1.bottom(0.5))
	p10_single.blow_out()
p10_single.drop_tip()

# Incubate at 4C, then heat shock.
p10_single.delay(minutes=30)
temp_deck.set_temperature(42)
p10_single.delay(minutes=1)
temp_deck.set_temperature(4)
p10_single.delay(minutes=5)

# Add lb.
p300_multi.pick_up_tip()
for i in range(0, num_cols):
	p300_multi.transfer(150, lb.bottom(), reaction_plate.wells(48 + i * 8).bottom(1), mix_after=(2, 150), new_tip='never')
	p300_multi.mix(2, 300, wash_0.bottom())
	p300_multi.blow_out()
	p300_multi.mix(2, 300, wash_1.bottom())
	p300_multi.blow_out()
p300_multi.drop_tip()

# Grow for 1 hr, adding water/mixing if necessary.
temp_deck.set_temperature(37)
p10_single.delay(minutes=60)

def spread_culture(source, dest, lb, dilute_after=True):
	p300_multi.mix(2, 150, source.bottom(0.5))
	p300_multi.aspirate(10, source.bottom(0.5))
	p300_multi.dispense(9, dest.top())
	p300_multi.dispense(1, dest.bottom(-1))
	if dilute_after:
		p300_multi.transfer(120, source.bottom(0.5), liquid_waste.bottom(), new_tip='never')
		p300_multi.mix(2, 300, wash_0.bottom())
		p300_multi.blow_out()
		p300_multi.mix(2, 300, wash_1.bottom())
		p300_multi.blow_out()
		p300_multi.transfer(120, lb, source.bottom(0.5), new_tip='never')

# Dilute and plate.
for i in range(0, num_cols):
	agar_plate = agar_plates[i // 3]
	agar_well_num = (i % 3) * 8 * 4
	p300_multi.pick_up_tip()
	source = reaction_plate.wells(48 + i * 8)
	spread_culture(source, agar_plate.wells(agar_well_num), lb)
	spread_culture(source, agar_plate.wells(agar_well_num + 8), lb)
	spread_culture(source, agar_plate.wells(agar_well_num + 16), lb)
	spread_culture(source, agar_plate.wells(agar_well_num + 24), lb, dilute_after=False)
	p300_multi.drop_tip()

