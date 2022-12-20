"""
This is a gap-fill script that invokes the Blender API (if present)
to convert a Collada 1.5 object (output from ArcGIS Pro but not widely
used in practice) to a Collada 1.4 object (which is more widely used).
The script is issued as an argument to an invocation of a background
(no GUI) instance of Blender, e.g.:

/path/to/blender.exe -b -P dae2dae.py file_to_be_converted.dae


import bpy
import sys
import os


class ColladaDowngrade:

    def __init__(self, input_dae):
        self.input_dae = input_dae
        self.input_path, self.input_fn = os.path.split(self.input_dae)
