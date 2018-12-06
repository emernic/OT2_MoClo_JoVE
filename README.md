# Modular Cloning with the OT2

This project enables end-to-end molecular cloning using the OT2 liquid handling robot by OpenTrons. This includes:
- Performing modular cloning (Golden Gate) reactions.
- Transforming plasmids into E. coli using heat shock.
- Plating transformations onto rectangular agar plates.
- Picking colonies and innoculating overnight cultures (requires separate imager).
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

## Modular Cloning / Transformation

### Initial setup

1. Prepare up to 2 CSV files (which can be produced in Excel) representing input plate maps. These plate maps may have up to 8 rows and 12 columns each, with each cell containing a plasmid name and empty wells left blank. These should represent 96-well microplate format plates of DNA parts at 2 fmol/ul.

2. Prepare 1 CSV file representing the combinations of parts to assemble, with each row representing one assembly. Each row should have N columns with the names of the parts to assemble (which must match the names in the plate maps of step 1).

### Generating protocol

3. Run the ot2_moclo_jove/moclo_transform/moclo_transform_generator.py using Python (e.g. typing `python3 moclo_transform_generator.py` in the command line). Select the plate map(s), combinations list, and an output folder for the protocol when prompted.

4. A protocol named `moclo_transform_protocol.py` should be saved in the output folder. See JoVE protocol video for details related to setting up the deck and running this protocol on the OT2.

## Colony Picking

### Initial setup

1. Edit ot2_moclo_jove/moclo_transform/data/settings.yaml based on your own preferences. In particular...
	- *plate_locations* should be adjusted to the locations (in pixels) of the A1 corner of each plate in your image. It is recommended to only use 1 plate per image for maximum accuracy, but multiple plates are supported.
	- *colony_regions* specifies (in mm relative to corner A1) the regions to search for colonies. For example, a grid of circular areas: `{type: circle, x: 10, y: 10, r: 50, rows: 5, columns: 10, x_spacing: 10, y_spacing: 10}` or a grid of rectangles `{type: rectangle, x_1: 10, y_1: 10, x_2: 15, y_2: 15, rows: 5, columns: 10, x_spacing: 10, y_spacing: 10}`.
	- *pixels_per_mm* should be calculated for your plate images (pixels per millimeter).
	- *rotate* should be adjusted to rotate your images such that well A1 of each plate is in the upper left hand corner.
	- *calibration_point_location* should be the relative location (in mm) of the point on the plate to which you calibrate the OT2 pipette. For example, this might be the upper-left corner of the rim of the plate, which might be at coordinates x: 1.1, y: 1.1.
	- *block_columns* and *block_rows* should match the dimensions of your culture block (changes not recommended).
	- *blur_radius*, *brightness*, *contrast*, and *inverted* can be tweaked to affect pre-processing of images to improve colony detection. You can take a look at the pre-processed images in the ot2_colony_picking/data/temp folder after running the colony picking script.
	- *opencfu_arg_string* can be used to pass arguments to OpenCFU to tweak colony identification (see [OpenCFU arguments documentation](https://github.com/qgeissmann/OpenCFU/blob/3f695e8c1c9f355aac953bd68d18cf7a0c619814/src/processor/src/ArgumentParser.cpp))
	- *colonies_to_pick* determines the max number of colonies to pick per region.

2. Optional: Save one or more background images in ot2_moclo_jove/colony_picking/data/background_images

3. Save image(s) of your plate(s) to the ot2_moclo_jove/colony_picking/data/images folder (this location can be changed in settings.yaml). By default, this program will use the most recently created images in this folder first.

### Generating protocol

1. Run ot2_moclo_jove/colony_picking/colony_pick_generator.py and follow instructions for:
	- Selecting an output folder for the generated OT2 protocol and culture block map.
	- Locating your OpenCFU installation folder (if not already set in settings.yaml)
	- Entering the number of agar plates you would like to pick colonies for (this many images from the images folder will be used).
	- Selecting input plate maps. You should select them in the same order you took the images (i.e. plate map 0 should correspond to the oldest image). Each plate map should be a CSV file of plasmid names where each name maps to one colony region on the plate (colony regions are defined in settings.yaml).

2. An output protocol should have been generated in the designated folder, as well as some previews images from the colony identification process (found in ot2_moclo_jove/colony_picking/data/temp) with colonies circled in green and colony regions outlined in red. See JoVE video for specifics of running the protocol on the OT2.
