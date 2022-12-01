import arcpy
from arcpy.sa import *
from datetime import datetime
import os
from pathlib import Path
import sys

arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension("3D")

# Disable cache files
sys.dont_write_bytecode = True


class ProjectionException(Exception):
    pass


class SurfaceImageToCollada(object):
    
    def __init__(self):
        """
        Converts surface raster and aligned image to a textured Collada model.
        """
        self.category = "3D Utilities"
        self.name = "SurfaceImageToCollada"
        self.label = "Surface and Image Rasters to Collada"
        self.description = "Converts surface raster and aligned image to a textured Collada model"
        self.canRunInBackground = False
        
    def getParameterInfo(self):
        
        param0 = arcpy.Parameter(
            displayName="Image Layer",
            name="img_in",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input"
        )
        
        param1 = arcpy.Parameter(
            displayName="Terrain Layer",
            name="terrain_in",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input"
        ) 
        
        param2 = arcpy.Parameter(
            displayName="Output Folder Name",
            name="folderout",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        ) 
        
        param3 = arcpy.Parameter(
            displayName="Rows",
            name="rows",
            datatype="GPLong",
            parameterType="Optional",
            direction="Input"
        ) 
        
        param4 = arcpy.Parameter(
            displayName="Columns",
            name="cols",
            datatype="GPLong",
            parameterType="Optional",
            direction="Input"
        ) 
        
        param5 = arcpy.Parameter(
            displayName="Z Value",
            name="z",
            datatype="GPLong",
            parameterType="Optional",
            direction="Input"
        ) 
        
        param6 = arcpy.Parameter(
            displayName="Quality",
            name="quality",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        
        param6.filter.type = "ValueList"
        param6.filter.list = ["Low", "Medium", "High", "Insane"]
        
        return [param0, param1, param2, param3, param4, param5, param6]
    
    def isLicensed(self):
        return True
    
    def updateParameters(self, parameters):
        return True
    
    def updateMessages(self, parameters):
        return True
    
    @staticmethod
    def now():
        return datetime.now().strftime("%Y%m%dT%H%M%S")
    
    @staticmethod
    def get_home_path():
        p = arcpy.mp.ArcGISProject("CURRENT").homeFolder
        return Path(p).resolve()
    
    def execute(self, parameters, messages):
        
        # Environments
        arcpy.env.overwriteOutput = True
        scratch = arcpy.env.scratchGDB
        
        # Do the work
        try:
            img_in = parameters[0].valueAsText
            terrain_in = parameters[1].valueAsText
            out_folder_name = parameters[2].valueAsText
            
            rows = parameters[3].value
            cols = parameters[4].value
            z = parameters[5].value
            
            if not rows:
                rows = 2
            if not cols:
                cols = 2
                
            q = parameters[6].valueAsText
            if q == "Low":
                z = 2
            elif q == "Medium":
                z = 1
            elif q == "High":
                z = .5
            elif q == "Insane":
                z = .05
                
            folder_out = os.path.join(SurfaceImageToCollada.get_home_path(), f"3D/{out_folder_name}")
            
            if not os.path.exists(folder_out):
                os.makedirs(folder_out)
                
            d = arcpy.Describe(img_in)
            layer_in_sr = d.spatialReference
            if layer_in_sr.factoryCode in [4326, 3857, None]:
                raise ProjectionException("Input data is not projected.  Please ensure all inputs are projected and retry.")
                
            # Get extent polygon
            p = arcpy.mp.ArcGISProject("CURRENT")
            
            arcpy.SetProgressor("default", "Getting extents...")
            extent_poly = p.activeView.camera.getExtent().polygon.projectAs(layer_in_sr)
            mask = arcpy.CopyFeatures_management(extent_poly, os.path.join(scratch, "mask"))
            
            # Prep rasters
            arcpy.SetProgressor("default", "Processing rasters...")
            img_lyr = arcpy.MakeRasterLayer_management(img_in)
            terrain_lyr = arcpy.MakeRasterLayer_management(terrain_in)
            
            img_xtract_full = ExtractByMask(img_lyr, mask)
            img_xtract = arcpy.ia.ExtractBand(img_xtract_full, [1, 2, 3])
            terrain_xtract = ExtractByMask(terrain_lyr, mask)
            
            # Convert image to JPG for painting Collada model
            jpg_out = os.path.join(folder_out, "paint.jpg")
            arcpy.CopyRaster_management(
                img_xtract, jpg_out, nodata_value="255", pixel_type="8_BIT_UNSIGNED", RGB_to_Colormap="NONE")
            
            # Create single flat .dae terrain for digitizing
            arcpy.SetProgressor("default", "Creating Collada flat...")
            tin_params = str(os.path.join(scratch, "mask")) + " Shape_Area Soft_Clip"
            tin_name = os.path.join(folder_out, "flatTIN")
            try:
                tin = arcpy.CreateTin_3d(
                    tin_name,
                    spatial_reference=layer_in_sr,
                    in_features=tin_params,
                    constrained_delaunay="DELAUNAY")
            except arcpy.ExecuteError:
                arcpy.AddWarning(arcpy.GetMessages())
                pass
            
            # Convert flat TIN to flat multipatch
            fm_name = os.path.join(scratch, "flat_mp")
            arcpy.InterpolatePolyToPatch_3d(tin, mask, fm_name, "", "1", "Area", "SArea", "0")
            
            # Convert flat multipatch to flat collada
            flat_dae_name = os.path.join(folder_out, "flat")
            arcpy.MultipatchToCollada_conversion(fm_name, flat_dae_name, "PREPEND_SOURCE_NAME", "")
