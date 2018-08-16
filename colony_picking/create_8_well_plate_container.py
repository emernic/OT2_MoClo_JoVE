# Running this protocol on the app will simply create the container we use for our 8 well agar plates.
# The OT2 thinks that this container is just a plate with 1 well, which we will use as a calibration reference.

from opentrons import labware

point_for_colony_picking = labware.create(
    'point-for-colony-picking',            # name of you container
    grid=(1, 1),                    # specify amount of (rows, columns)
    spacing=(0, 0),               # distances (mm) between each (row, column)
    diameter=0,                     # diameter (mm) of each well on the plate
    depth=0,                       # depth (mm) of each well on the plate
    volume=0)