# Modular Cloning with the OT2

**This project is still in active development and is not yet ready for use.**

This project allows users to do end-to-end molecular cloning using the OT2 liquid handling robot by OpenTrons. This includes:
- Performing modular cloning (Golden Gate) reactions.
- Transforming into E. coli using heat shock.
- Plating transformations onto rectangular agar plates.
- Picking colonies and innoculating overnight cultures (requires OpenCFU & separate imager).
- Plasmid minipreps using magnetic beads (requires Mag Deck and some manual centrifugation steps).

All code for this project is freely distributed for academic and commercial uses under the MIT license.

## General Installation

1. Confirm that you have [Python 3](https://www.python.org/downloads/) installed.

2. Install from setup.py. For example, by typing in the command line while in the package folder:
~~~~
python3 setup.py install
~~~~

3. If using the colony picking module, install [OpenCFU](https://sourceforge.net/projects/opencfu/files/) (for Windows or Linux).

4. It is highly recommended you watch the JoVE video tutorial on how to configure the software for your set up LINK TO VIDEO HERE.

## Colony Picking

### Initial setup for colony picking

1. Edit ot2_moclo_jove/data/settings.yaml based on your own set up. In particular...
	- *plate_locations* should be adjusted to the locations (in pixels) of the A1 corner of each plate in your image. It is recommended to only use 1 plate per image.
	- *colony_regions* specifies the regions to search for colonies. For example, a grid of circular areas: `{type: circle, x: 10, y: 10, r: 50, rows: 5, columns: 10, x_spacing: 10, y_spacing: 10}` or a grid of rectangles `{type: rectangle, x_1: 10, y_1: 10, x_2: 15, y_2: 15, rows: 5, columns: 10, x_spacing: 10, y_spacing: 10}`.
	- *pixels_per_mm* should be calculated for your plate images (pixels per millimeter).
	- *rotate* should be adjusted to rotate your images such that well A1 of each plate is in the upper left hand corner.
	- *calibration_point_location* should be the relative location (in mm) of the point to which you calibrate the OT2 pipette. For example, this might be the lower-left corner of the rim of the plate, which might be x: 1.1, y: 1.1.
	- *block_columns* and *block_rows* should match the dimensions of your culture block.
	- *blur_radius*, *brightness*, *contrast*, and *inverted* can be tweaked to affect pre-processing of images if you are getting too many or too few colonies detected. You can take a look at the pre-processed images in the ot2_colony_picking/data/temp folder after running the colony picking script.
	- *opencfu_arg_string* can be used to pass arguments to OpenCFU to tweak colony identification (see [OpenCFU arguments documentation](https://github.com/qgeissmann/OpenCFU/blob/3f695e8c1c9f355aac953bd68d18cf7a0c619814/src/processor/src/ArgumentParser.cpp))
	- *colonies_to_pick* determines the max number of colonies to pick per region.

2. Optional: Save one or more background images in ot2_moclo_jove/colony_picking/data/background_images

### Generating protocol for colony picking

1. Save an image of your plates to the ot2_moclo_jove/colony_picking/data/images folder (this location can be changed in settings.yaml). By default, this program will use the most recently created images in this folder.

2. Run ot2_moclo_jove/colony_picking/colony_pick_generator.py and follow instructions for:
	- Selecting an output folder for the generated OT2 protocol and culture block map.
	- Locating your OpenCFU installation folder (if not already set in settings.yaml)
	- Entering the number of agar plates you would like to pick colonies for.
	- Selecting input plate maps. You should select them in the same order you took the images (i.e. plate map 0 should correspond to the oldest image). Each plate map should be a CSV file of plasmid names for each culture spot on the input plate.

3. An output protocol should have been generated in the designated folder, as well as some previews images from the colony identification process (found in ot2_moclo_jove/colony_picking/data/temp) with colonies circled in green. Confirm that the output script is correct and then run it on the OT2.

## TODO:

- Reorganize interface into a tkinter interface (which is used if the generator functions are run directly), and a pure Python interface (writing all the functions such that this project could be imported by others and used in a larger Python project).
