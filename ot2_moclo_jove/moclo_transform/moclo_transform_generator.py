import os
import tkinter
from tkinter import filedialog, messagebox
import csv
import json
import yaml

#################################################################################################################
# Constants
#################################################################################################################

CONFIG_PATH = "data/settings.yaml"


#################################################################################################################
# Main function of script
#################################################################################################################

def main():

	###### GETTING USER INPUT ######
	config = get_config(CONFIG_PATH)
	dna_plate_map_filenames = ask_dna_plate_map_filenames()
	combinations_filename = ask_combinations_filename()

	# Load in CSV files as a dict containing lists of lists.
	dna_plate_map_dict = generate_plate_maps(dna_plate_map_filenames)
	combinations_to_make = generate_combinations(combinations_filename)

	# Generate and save output plate maps.
	generate_and_save_output_plate_maps(combinations_to_make, config['output_folder_path'])

	# Create a protocol file and hard code the plate maps into it.
	create_protocol(dna_plate_map_dict, combinations_to_make, config['protocol_template_path'], config['output_folder_path'])


#################################################################################################################
# Functions for getting user input
#################################################################################################################

def get_config(config_path):
	# Load settings from file.
	config = yaml.safe_load(open(config_path))

	# Create a tkiner window and hide it (this will allow us to create dialog boxes)
	window = tkinter.Tk()
	window.withdraw()

	# Ask user to set output folder if not set.
	if not config['output_folder_path']:
		messagebox.showinfo("Choose output folder", "You will now select the folder to save the protocol and plate maps to. This can be changed later by editing settings.yaml in the OT2_MoClo_JoVE/moclo_transform/data folder.")
		config['output_folder_path'] = filedialog.askdirectory(title = "Choose output folder")
		with open(config_path, "w+") as yaml_file:
			yaml_file.write(yaml.dump(config))
	return config

def ask_dna_plate_map_filenames():
	# Create tkinter window in background to allow us to make dialog boxes.
	window = tkinter.Tk()
	window.withdraw()

	# Open dialog boxes asking user for dna plate maps.
	dna_plate_map_filenames = filedialog.askopenfilenames(title = "Select DNA plate maps", filetypes = (("CSV files","*.CSV"),("all files","*.*")))
	return dna_plate_map_filenames

def ask_combinations_filename():
	# Create tkinter window in background to allow us to make dialog boxes.
	window = tkinter.Tk()
	window.withdraw()

	# Open dialog boxes asking user for combinations file.
	combinations_filename = filedialog.askopenfilename(title = "Select file containing combinations to make.", filetypes = (("CSV files","*.CSV"),("all files","*.*")))
	return combinations_filename

def generate_plate_maps(filenames):
	plate_maps = {}
	for filename in filenames:
		plate_map = []
		with open(filename, "r") as file:
			for row in csv.reader(file, dialect='excel'):
				plate_map.append(row)
		plate_name = os.path.splitext(os.path.basename(filename))[0]
		plate_maps[plate_name] = plate_map
	return plate_maps

def generate_combinations(combinations_filename):
	combinations_to_make = []
	with open(combinations_filename, "r") as f:
		for row in csv.reader(f, dialect='excel'):
			if row[0]:
				combinations_to_make.append({
					"name": row[0],
					"parts": [x for x in row[1:] if x]
				})
	print("combinations_to_make", combinations_to_make)
	return combinations_to_make


#################################################################################################################
# Functions for creating output files
#################################################################################################################

def generate_and_save_output_plate_maps(combinations_to_make, output_folder_path):
	# Split combinations_to_make into 8x3 plate maps.
	output_plate_maps_flipped = []
	for i, combo in enumerate(combinations_to_make):
		name = combo["name"]
		if i % 24 == 0:
			# new plate
			output_plate_maps_flipped.append([[name]])
		elif i % 8 == 0:
			# new column
			output_plate_maps_flipped[-1].append([name])
		else:
			output_plate_maps_flipped[-1][-1].append(name)
	print("output_plate_maps_flipped", output_plate_maps_flipped)
	# Correct row/column flip.
	output_plate_maps = []
	for plate in output_plate_maps_flipped:
		corrected_plate = []
		for i, row in enumerate(plate):
			for j, element in enumerate(row):
				if j >= len(corrected_plate):
					corrected_plate.append([element])
				else:
					corrected_plate[j].append(element)
		output_plate_maps.append(corrected_plate)
	print("output_plate_maps", output_plate_maps)
	for i, plate in enumerate(output_plate_maps):
		output_filename = os.path.join(output_folder_path, "Agar_plate_{0}.csv".format(i))
		with open(output_filename, 'w+', newline='') as f:
			writer = csv.writer(f)
			print(plate)
			writer.writerows(plate)

def create_protocol(dna_plate_map_dict, combinations_to_make, protocol_template_path, output_folder_path):
	# Get the contents of colony_pick_template.py, which contains the body of the protocol.
	with open(protocol_template_path) as template_file:
		template_string = template_file.read()

	with open(output_folder_path + '/' + 'moclo_transform_protocol.py', "w+") as protocol_file:
		# Paste in plate maps at top of file.
		protocol_file.write('dna_plate_map_dict = ' + json.dumps(dna_plate_map_dict) + '\n\n')

		protocol_file.write('combinations_to_make = ' + json.dumps(combinations_to_make) + '\n\n')

		# Paste the rest of the protocol.
		protocol_file.write(template_string)


#################################################################################################################
# Call main function
#################################################################################################################

if __name__ == '__main__':
    main()
