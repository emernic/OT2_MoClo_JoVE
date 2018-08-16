import os
import tkinter
from tkinter import filedialog, messagebox
import subprocess
import sys
from io import StringIO
import csv
import json
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance
import math
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

	image_filenames = get_image_filenames(config['image_folder_path'])
	mask_filenames = get_mask_filenames(config['mask_folder_path'])
	background_filenames = get_background_filenames(config['background_folder_path'])

	num_plates = ask_num_plates()
	source_plate_filenames = ask_source_plate_filenames(num_plates)


	###### PRE-PROCESSING IMAGES ######
	preprocessed_image_filenames = preprocess_images(
		image_filenames,
		config['temp_folder_path'],
		inverted=config['inverted'],
		blur_radius=config['blur_radius'],
		brightness=config['brightness'],
		contrast=config['contrast'],
		background_filenames=background_filenames)

	plates = generate_plates(preprocessed_image_filenames, source_plate_filenames, num_plates, config['plate_locations'])

	transformed_mask_filenames = transform_masks(plates, mask_filenames, config['temp_folder_path'], config['rotate'])


	###### LOCATING COLONIES WITH OPENCFU ######
	culture_blocks_dict = locate_colonies(
		plates,
		config['calibration_point_location'],
		transformed_mask_filenames,
		config['temp_folder_path'],
		config['opencfu_folder_path'],
		config['opencfu_arg_string'],
		config['colonies_to_pick'],
		config['pixels_per_mm'],
		config['block_columns'],
		config['block_rows'],
		rotate=config['rotate'])


	###### CREATING OUTPUT BLOCK MAPS AND PROTOCOL FILE ######
	create_block_maps(culture_blocks_dict, config['output_folder_path'])
	create_protocol(culture_blocks_dict, config['protocol_template_path'], config['output_folder_path'])

	if not config['keep_temp_files']:
		delete_temp_files(config['temp_folder_path'])


#################################################################################################################
# Functions for getting user input
#################################################################################################################

def get_config(config_path):
	# Load settings from file.
	config = yaml.safe_load(open(config_path))

	# Create a tkiner window and hide it (this will allow us to create dialog boxes)
	window = tkinter.Tk()
	window.withdraw()

	# Ask user to set image folder if not set.
	if not config['image_folder_path']:
		messagebox.showinfo("Choose image folder", "You will now select the folder containing saved plate images. This can be changed later by editing settings.yaml in the OT2_MoClo_JoVE/colony_picking/data folder.")
		config['image_folder_path'] = filedialog.askdirectory(title = "Choose image folder")
		with open(config_path, "w+") as yaml_file:
			yaml_file.write(yaml.dump(config))
	
	# Ask user to set output folder if not set.
	if not config['output_folder_path']:
		messagebox.showinfo("Choose output folder", "You will now select the folder to save the protocol and plate maps to. This can be changed later by editing settings.yaml in the OT2_MoClo_JoVE/colony_picking/data folder.")
		config['output_folder_path'] = filedialog.askdirectory(title = "Choose output folder")
		with open(config_path, "w+") as yaml_file:
			yaml_file.write(yaml.dump(config))

	return config

def get_image_filenames(image_folder_path):
	# Get all images from folder and sort by creation time.
	image_filenames = [(image_folder_path + '/' + image_name) for image_name in os.listdir(image_folder_path)]
	image_filenames.sort(key=lambda x: os.path.getmtime(x))
	return image_filenames

def get_mask_filenames(mask_folder_path):
	return [(mask_folder_path + '/' + mask_name) for mask_name in os.listdir(mask_folder_path)]

def get_background_filenames(background_folder_path):
	# Background image filenames (optional). If multiple are found they will be averaged.
	return [(background_folder_path + '/' + image_name) for image_name in os.listdir(background_folder_path)]

def ask_num_plates():
	# Ask user in command line for number of plates
	return int(input("How many agar plates are you picking colonies for?: "))

def ask_source_plate_filenames(num_plates):
	# Create tkinter window in background to allow us to make dialog boxes.
	window = tkinter.Tk()
	window.withdraw()

	# Open dialog boxes asking user for plate maps.
	source_plate_filenames = []
	for i in range(0, num_plates):
		source_plate_filenames.append(filedialog.askopenfilename(title = "Select plate map {0}".format(i), filetypes = (("CSV files","*.CSV"),("all files","*.*"))))

	return source_plate_filenames


#################################################################################################################
# Functions for pre-processing images
#################################################################################################################

# Blur slightly (improves background subtraction and colony detection).
def blur(image, blur_radius):
	return image.filter(ImageFilter.GaussianBlur(radius=blur_radius))

def brightness_contrast(image, brightness, contrast):
	# Adjust brightness and contrast to improve detection
	image = ImageEnhance.Contrast(image).enhance(contrast)
	image = ImageEnhance.Brightness(image).enhance(brightness)
	return image

def blend(images, blur_radius):
	average = blur(images[0], blur_radius)
	for i in range(1, len(images)):
	    img = blur(images[i], blur_radius)
	    average = Image.blend(average, img, 1.0 / float(i + 1))
	return average

# Processes images with various functions to improve colony detection. Saves to temp_folder_path.
def preprocess_images(image_filenames, temp_folder_path, inverted=False, blur_radius=0.0, brightness=1.0, contrast=1.0, background_filenames=None):
	
	preprocessed_image_filenames = []

	for image_filename in image_filenames:
		
		image = Image.open(image_filename)
		image = blur(image, blur_radius)
		image = brightness_contrast(image, brightness, contrast)

		if background_filenames:
			background_images = [Image.open(x) for x in background_filenames]
			average_background = blend(background_images, blur_radius)

			if inverted:
				image = ImageChops.subtract(average_background, image)
			else:
				image = ImageChops.subtract(image, average_background)

		# Save in temporary folder.
		preprocessed_image_filename = temp_folder_path + '/' + os.path.basename(image_filename)
		image.save(preprocessed_image_filename)

		preprocessed_image_filenames.append(preprocessed_image_filename)

	return preprocessed_image_filenames

# Used to rotate and scale image masks correctly onto the image.
def transform_image(image, angle = 0.0, center = (0.0, 0.0), new_center = (0.0, 0.0), scale = (1.0, 1.0)):
        angle = -angle / 180.0 * math.pi
        (x, y) = center
        (nx, ny) = new_center
        (sx, sy) = scale
        cosine = math.cos(angle)
        sine = math.sin(angle)
        a = cosine / sx
        b = sine / sx
        c = x - nx * a - ny * b
        d = -sine / sy
        e = cosine / sy
        f = y - nx * d - ny * e
        return image.transform(image.size, Image.AFFINE, (a,b,c,d,e,f), resample=Image.BICUBIC)

def transform_mask(mask_filename, plate, temp_folder_path, rotate):
	image = Image.open(plate['image_filename'])
	image_width, image_height = image.size

	# Make the mask the same size as the image and transform to correct position in plate.
	mask = Image.open(mask_filename)
	mask = mask.crop((0, 0, image_width, image_height))
	mask = transform_image(mask, angle=-rotate, new_center=(plate['location_in_image']['x'], plate['location_in_image']['y']))

	# Save the adjusted mask as a temporary file.
	image_basename = os.path.splitext(os.path.basename(plate['image_filename']))[0]
	transformed_mask_filename = temp_folder_path + '/' + image_basename + os.path.basename(mask_filename)
	transformed_mask_filename = os.path.abspath(transformed_mask_filename)
	mask.save(transformed_mask_filename)

	return transformed_mask_filename

def transform_masks(plates, mask_filenames, temp_folder_path, rotate):
	transformed_mask_filenames = []
	for plate in plates:
		for mask_filename in mask_filenames:
			transformed_mask_filenames.append(transform_mask(mask_filename, plate, temp_folder_path, rotate))

	return transformed_mask_filenames


#################################################################################################################
# Functions for locating colonies with OpenCFU
#################################################################################################################

# Generates a list of plates, their images filenames and source plate (map) filenames, and their locations within their source images.
def generate_plates(preprocessed_image_filenames, source_plate_filenames, num_plates, plate_locations):
	
	plates_per_image = len(plate_locations)
	#num_images = int(num_plates // plates_per_image) + (num_plates % plates_per_image > 0)

	plates = []
	plate_index = 0
	for preprocessed_image_filename in preprocessed_image_filenames:
		for i in range(0, plates_per_image):
			if plate_index < num_plates:
				plates.append({
					'image_filename' : preprocessed_image_filename,
					'source_plate_filename' : source_plate_filenames[plate_index],
					'location_in_image' : plate_locations[i]
				})
				plate_index += 1

	return plates

# Run opencfu for this section of the agar plate and return an iterable reader of output.
def run_opencfu(opencfu_folder_path, image_filename, mask_filename, arg_string):
	shell_command = 'cd "{0}" && opencfu -i "{1}" -m "{2}" {3}'.format(opencfu_folder_path, image_filename, mask_filename, arg_string)
	raw_opencfu_output = subprocess.check_output(args = shell_command, shell = True)
	f = StringIO(raw_opencfu_output.decode("utf-8"))
	return csv.DictReader(f, delimiter = ',')

# Make a list of colony coordinates (in image pixels and in mm from plate origin) from opencfu output.
def make_colony_list(reader, plate, calibration_point_location, pixels_per_mm, rotate):
	colony_list = []
	for row in reader:
		if row['IsValid'] == '1':
			x = float(row['X'])
			y = float(row['Y'])

			# Colony coordinates are still in pixels relative to the corner of the image, we need them in mm relative
			# to their locations in each plate.
			translated_x = x - plate['location_in_image']['x']
			translated_y = y - plate['location_in_image']['y']
			cosine = math.cos(-rotate)
			sine = math.sin(-rotate)
			rotated_x = translated_x*cosine - translated_y*sine
			rotated_y = translated_y*cosine + translated_x*sine
			mm_x = rotated_x / pixels_per_mm
			mm_y = rotated_y / pixels_per_mm

			# Lastly, convert from "mm away from upper left corner of plate" (with down being positive y) 
			# to "mm away from the leftmost crossing plastic divisions in the plate" (with up being positive y)
			# because this is how positions are understood by the robot.
			final_x = mm_x - calibration_point_location['x']
			final_y = calibration_point_location['y'] - mm_y
			colony_list.append({'x': final_x, 'y': final_y, 'x_in_image': x, 'y_in_image': y})

	return colony_list

# Draws a list of colony locations onto a preview file.
def draw_colony_list(colony_list, original_filename, preview_filename):

	# Create preview image of colony picking
	original = Image.open(original_filename)
	im = original.copy()
	draw = ImageDraw.Draw(im)

	for colony in colony_list:
		x = colony['x_in_image']
		y = colony['y_in_image']
		# draw point on image preview
		draw.ellipse((x-4, y-4, x+4, y+4), outline = (255, 0, 0, 255))

	# Save image preview
	im.save(preview_filename)

def measure_colony_distances(colony_list):
	# Find the minimum distance from other colonies for each colony
	colonies_with_distances = []
	for colony_1 in colony_list:
		colonies_with_distances.append(colony_1)
		colonies_with_distances[-1]['dist'] = 10000
		for colony_2 in colony_list:
			if not colony_1 == colony_2:
				dist = ((colony_2['x']-colony_1['x'])**2 + (colony_2['y']-colony_1['y'])**2)**0.5
				if dist < colonies_with_distances[-1]['dist']:
					colonies_with_distances[-1]['dist'] = dist

	return colonies_with_distances

def get_plasmid_name(source_plate_filename, transformed_mask_filename):
	# Get name of the plasmid by reading user-supplied plate map.
	with open(source_plate_filename, newline='', encoding="utf-8-sig") as csvfile:
		csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
		mask_base_filename = os.path.splitext(os.path.basename(transformed_mask_filename))[0]
		alphanum = mask_base_filename.split("_")[-1]
		mask_row = ord(alphanum[0].lower())-97
		mask_col = int(alphanum[1:]) - 1
		plasmid_name = list(csvreader)[mask_row][mask_col]

	return plasmid_name

# Output of this function is a dict of output culture blocks. Each culture block is represented by a list of lists. 
# Each entry contains the name of the plasmid ('name'), the agar plate it came from ('source'), and the x y position
# in mm of the colony it came from ('x', 'y', and 'z').
# For example...
# culture_blocks_dict = {
# 	'culture_block_0': [
# 		[
# 			{'name': 'plasmid_name_1', 'source': 'agar_plate_0', 'x': 12.123, 'y': 14.13, 'z': -8.0}, 
# 			{'name': 'plasmid_name_1', 'source': 'agar_plate_0', 'x': 15.12, 'y': 12.0, 'z': -8.0}
# 		],
# 		[
# 			{'name': 'plasmid_name_13', 'source': 'agar_plate_3', 'x': 14.123, 'y': 17.13, 'z': -8.0},
# 			{'name': 'plasmid_name_14', 'source': 'agar_plate_3', 'x': 10.1, 'y': 20.01, 'z': -8.0}
# 		]
# 	],
# 	'culture_block_1': [
# 		[
# 			{'name': 'plasmid_name_14', 'source': 'agar_plate_3', 'x': 12.3, 'y': 15.13, 'z': -8.0}, 
# 			{'name': 'plasmid_name_15', 'source': 'agar_plate_3', 'x': 15.12, 'y': 12.0, 'z': -8.0}
# 		],
# 		[
# 			{'name': 'plasmid_name_17', 'source': 'agar_plate_4', 'x': 17.123, 'y': 11.13, 'z': -8.0},
# 			{'name': 'plasmid_name_18', 'source': 'agar_plate_4', 'x': 20.1, 'y': 15.01, 'z': -8.0}
# 		]
# 	],
# }
def locate_colonies(plates, calibration_point_location, transformed_mask_filenames, temp_folder_path, opencfu_folder_path, opencfu_arg_string, colonies_to_pick, pixels_per_mm, block_columns, block_rows, rotate=0.0):
	# Tracking output block number, row, and column.
	n = 0
	i = 0
	j = 0
	culture_blocks_dict = {}
	culture_blocks_dict['culture_block_0'] = []
	culture_blocks_dict['culture_block_0'].append([])

	for plate in plates:

		source_plate_filename = plate['source_plate_filename']

		for transformed_mask_filename in transformed_mask_filenames:

			reader = run_opencfu(opencfu_folder_path, os.path.abspath(plate['image_filename']), transformed_mask_filename, opencfu_arg_string)

			colony_list = make_colony_list(reader, plate, calibration_point_location, pixels_per_mm, rotate)

			mask_base_filename = os.path.splitext(os.path.basename(transformed_mask_filename))[0]
			mask_abbreviation = mask_base_filename.split("_")[-1]
			image_base_filename = os.path.splitext(os.path.basename(plate['image_filename']))[0]
			preview_filename = temp_folder_path + '/' + image_base_filename + '_{0}_preview.png'.format(mask_abbreviation)
			draw_colony_list(colony_list, plate['image_filename'], preview_filename)

			colonies_with_distances = measure_colony_distances(colony_list)

			sorted_colonies_with_distances = sorted(colonies_with_distances, key=lambda x: x['dist'], reverse=True)

			plasmid_name = get_plasmid_name(source_plate_filename, transformed_mask_filename)

			selected_colonies = sorted_colonies_with_distances[:colonies_to_pick]

			if plasmid_name:
				for colony in selected_colonies:
					culture_blocks_dict['culture_block_{0}'.format(n)][i].append({
						'name': plasmid_name, 
						'source': 'plate_{0}'.format(os.path.splitext(os.path.basename(source_plate_filename))[0]), 
						'x': colony['x'],
						'y': colony['y']
					})

					if j == block_columns:
						if i == block_rows:
							n += 1
							i = 0
							culture_blocks_dict['culture_block_{0}'.format(n)] = []
						else:
							i += 1
						j = 0
						culture_blocks_dict['culture_block_{0}'.format(n)].append([])
					else:
						j += 1

	return culture_blocks_dict

def delete_temp_files(temp_folder_path):
	temp_files = [file for file in os.listdir(temp_folder_path)]
	for file in temp_files:
	    os.remove(os.path.join(temp_folder_path, file))


#################################################################################################################
# Functions for creating output files
#################################################################################################################

def create_block_maps(culture_blocks_dict, output_folder_path):
	for block_name, block_map in culture_blocks_dict.items():
		with open(output_folder_path + '/' + '{0}.csv'.format(block_name), 'w+') as block_map_file:
			writer = csv.writer(block_map_file)
			for row in block_map:
				writer.writerow([x['name'] for x in row])

def create_protocol(culture_blocks_dict, protocol_template_path, output_folder_path):
	# Get the contents of colony_pick_template.py, which contains the body of the protocol.
	with open(protocol_template_path) as template_file:
		template_string = template_file.read()

	with open(output_folder_path + '/' + 'colony_pick_protocol.py', "w+") as protocol_file:
		# Paste colony locations dictionary into output file.
		protocol_file.write("culture_blocks_dict = " + json.dumps(culture_blocks_dict) + "\n\n")

		# Paste the rest of the protocol.
		protocol_file.write(template_string)


#################################################################################################################
# Call main function
#################################################################################################################

if __name__ == '__main__':
    main()