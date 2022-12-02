import arcpy
import os
import subprocess
import sys

#Disable cache file writing
sys.dont_write_bytecode = True

# Local imports
scripts_path = os.path.join(os.path.dirname(__file__), "scripts")
sys.path.append(scirpts_path)

import add_coordinate_attribute
import gets_som_wfs
import small_arms_range_rings
import utmizer
import surface_and_image_to_collada
import osrm_for_arcgis
import armor
import arcspy
import ground_photos
import make_ccm

ArcSpy = arcspy.ArcSpy
CoordsToAttributeTable = add_coordinate_attribute.CoordsToAttributeTable
GETSSOM = gets_som_wfs.GETSSOM
OSRM = osrm_for_arcgis.OSRM
SmallArmsRangeRings = small_arms_range_rings.SmallArmsRangeRings
SurfaceImageToCollada = surface_and_image_to_collada.SurfaceImageToCollada
UTMizer = utmizer.UTMizer
AMOR = armor.AreaMaxRiseOverRun
PHOTOSEARCH = ground_photos.PHOTOSEARCH
BuildCCM = make_ccm.BuildCCM


class Toolbox(object):
    
    def __init__(self):
        self.label = "IGEA GIS Tools"
        self.alias = "IGEAGISTools"
        self.tools = [
            AMROR,
            ArcSpy,
            BuildCCM,
            CoordsToAttributeTable,
            GETSSOM,
            OSRM,
            PHOTOSEARCH,
            SmallArmsRangeRings,
            SurfaceImageToCollada,
            UTMizer
        ]
