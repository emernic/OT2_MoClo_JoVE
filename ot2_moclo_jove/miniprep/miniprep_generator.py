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

	culture_block_filenames = ask_culture_block_filenames()

	# Load in CSV files as a dict containing lists of lists.
	plate_maps = generate_plate_maps(culture_block_filenames)

	# Associates an output plate filename to each plate map.
	plate_maps = add_output_plate_names(plate_maps, config['output_folder_path'])

	# Save output plate maps.
	save_plate_maps(plate_maps)

	# Create a protocol file and hard code the plate maps into it.
	create_protocol(plate_maps, config['protocol_template_path'], config['output_folder_path'])

	# Write the contents of miniprep_template.py (which contains the body of the protocol) to the new protocol file.


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
		messagebox.showinfo("Choose output folder", "You will now select the folder to save the protocol and plate maps to. This can be changed later by editing settings.yaml in the OT2_MoClo_JoVE/miniprep/data folder.")
		config['output_folder_path'] = filedialog.askdirectory(title = "Choose output folder")
		with open(config_path, "w+") as yaml_file:
			yaml_file.write(yaml.dump(config))

	return config

def ask_culture_block_filenames():
	# Create tkinter window in background to allow us to make dialog boxes.
	window = tkinter.Tk()
	window.withdraw()

	# Open dialog boxes asking user for culture block maps.
	culture_block_filenames = filedialog.askopenfilenames(title = "Select culture block maps", filetypes = (("CSV files","*.CSV"),("all files","*.*")))

	return culture_block_filenames

def generate_plate_maps(filenames):
	plate_maps = []
	for filename in filenames:
		plate_map = {}
		plate_map['culture_block_name'] = filename
		plate_map['map'] = []
		with open(filename) as file:
			for row in csv.reader(file, dialect='excel'):
				plate_map['map'].append(row)
		plate_maps.append(plate_map)

	return plate_maps

# Implicitly assumes input and output plates are identical.
def add_output_plate_names(plate_maps, output_folder_path):
	plate_maps_with_outputs = []
	for i, plate_map in enumerate(plate_maps):
		plate_map_with_output = plate_map
		plate_map_with_output['plasmid_plate_name'] = output_folder_path + '/' + 'plasmid_plate_{0}.csv'.format(i)
		plate_maps_with_outputs.append(plate_map_with_output)

	return plate_maps_with_outputs


#################################################################################################################
# Functions for creating output files
#################################################################################################################

def save_plate_maps(plate_maps):
	for plate_map in plate_maps:
		with open(plate_map['plasmid_plate_name'], 'w+') as plasmid_plate_map_file:
			writer = csv.writer(plasmid_plate_map_file)
			writer.writerows(plate_map['map'])

def create_protocol(plate_maps, protocol_template_path, output_folder_path):
	# Get the contents of colony_pick_template.py, which contains the body of the protocol.
	with open(protocol_template_path) as template_file:
		template_string = template_file.read()

	with open(output_folder_path + '/' + 'miniprep_protocol.py', "w+") as protocol_file:
		# Paste in plate maps at top of file.
		protocol_file.write(json.dumps(plate_maps) + '\n\n')

		# Paste the rest of the protocol.
		protocol_file.write(template_string)


#################################################################################################################
# Call main function
#################################################################################################################

if __name__ == '__main__':
    main()