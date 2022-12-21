"""
This is a gap-fill script that invokes the Blender API (if present)
to convert a Collada 1.5 object (output from ArcGIS Pro but not widely
used in practice) to a Collada 1.4 object (which is more widely used).
The script is issued as an argument to an invocation of a background
(no GUI) instance of Blender, e.g.:

/path/to/blender.exe -b -P dae2dae.py file_to_be_converted.dae
"""

import bpy
import sys
import os


class ColladaDowngrade:

    def __init__(self, input_dae):
        self.input_dae = input_dae
        self.input_path, self.input_fn = os.path.split(self.input_dae)
        self.fn_only, self.ext = os.path.splitext(self.input_fn)
        self.output_dae = os.path.join(self.input_path, f"{self.fn_only}_14{self.ext}")
        self.remove_cube()
        self.load_dae()
        self.save_dae()
        
    def load_dae(self):
        return bpy.ops.wm.collada_import(filepath=self.input_dae)
        
    def remove_cube(self):
        if "Cube" in bpy.data.meshes:
            cubemesh = bpy.data.meshes["Cube"]
            bpy.data.meshes.remove(cubemesh)
        return True
        
    def save_dae(self):
        return bpy.ops.wm.collada_export(filepath=self.output_dae)
        
        
if __name__ == "__main__":
    ColladaDowngrade(sys.argv[4])

