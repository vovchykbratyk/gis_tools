import arcpy
import os
import subprocess
import sys

#Disable cache file writing
sys.dont_write_bytecode = True

# Local imports
# scripts_path = os.path.join(os.path.dirname(__file__), "scripts")
# sys.path.append(scripts_path)

import scripts.add_coordinate_attribute
import scripts.amror
import scripts.canopy
import scripts.small_arms_range_rings
import scripts.terrain_and_image_to_collada
import scripts.utmizer


# import add_coordinate_attribute
# import amror
# import canopy
# import small_arms_range_rings
# import terrain_and_image_to_collada
# import utmizer

CoordsToAttributeTable = scripts.add_coordinate_attribute.CoordsToAttributeTable
AMROR = scripts.amror.AreaMaxRiseOverRun
CHM = scripts.canopy.CHM
SmallArmsRangeRings = scripts.small_arms_range_rings.SmallArmsRangeRings
TerrainImageToCollada = scripts.terrain_and_image_to_collada.TerrainImageToCollada
UTMizer = scripts.utmizer.UTMizer
#PHOTOSEARCH = ground_photos.PHOTOSEARCH
#BuildCCM = make_ccm.BuildCCM


class Toolbox(object):
    
    def __init__(self):
        self.label = "IGEA GIS Tools"
        self.alias = "IGEAGISTools"
        self.tools = [
            AMROR,
            CHM,
            CoordsToAttributeTable,
            SmallArmsRangeRings,
            TerrainImageToCollada,
            UTMizer
        ]
