import arcpy
from arcpy.sa import *
from datetime import datetime
import json
import os
from pathlib import Path, PureWindowsPath
import subprocess
import sys

# Local imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from userprefs import UserPrefs

arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension("3D")

# Disable cache files
sys.dont_write_bytecode = True

# Globals
DAE_DOWNGRADE_SCRIPT = os.path.join(os.path.dirname(__file__), 'blender', 'dae2dae.py')
USER_PREFS_PATH = UserPrefs().base


class ProjectionException(Exception):
    pass


class TerrainImageToCollada(object):
    
    def __init__(self):
        """
        Converts surface raster and aligned image to a textured Collada model.
        """
        self.category = "3D Utilities"
        self.name = "TerrainImageToCollada"
        self.label = "Terrain and Image Rasters to Collada"
        self.description = "Converts terrain raster and aligned image to a Collada model and texture"
        self.canRunInBackground = False
        
    def getParameterInfo(self):
        """
        Define parameters
        """
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
            displayName="Vertical Quality",
            name="quality",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )                
        
        param3.filter.type = "ValueList"
        param3.filter.list = ["Low", "Medium", "High", "Insane"]

        param4 = arcpy.Parameter(
            category="Advanced",
            displayName="Add/Update Path to Blender?",
            name="update_blender",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
        )

        param5 = arcpy.Parameter(
            category="Advanced",
            displayName="Path to Blender Executable",
            name="blenderpath",
            datatype="DEFile",
            parameterType="Optional",
            direction="Input"
        )
        
        return [param0, param1, param2, param3, param4, param5]
     
    def isLicensed(self):
        return True
    
    def updateParameters(self, parameters):
        return True
    
    def updateMessages(self, parameters):
        # Check if both layers are projected
        if parameters[0].altered:
            img_in_sr = arcpy.Describe(parameters[0].valueAsText).spatialReference
            if img_in_sr.type == "Geographic":
                parameters[0].setErrorMessage("Input image must be projected.")
                
            if parameters[1].altered:
                terr_in_sr = arcpy.Describe(parameters[1].valueAsText).spatialReference
                if terr_in_sr.factoryCode != img_in_sr.factoryCode:
                    if terr_in_sr.type != "Geographic":  # Only checking for different projections here
                        parameters[1].setErrorMessage(f"Input terrain projection (EPSG:{terr_in_sr.factoryCode}) does not match input image (EPSG:{img_in_sr.factoryCode})")
        if parameters[1].altered:
            terr_in_sr = arcpy.Describe(parameters[1].valueAsText).spatialReference
            if terr_in_sr.type == "Geographic":
                parameters[1].setErrorMessage("Input terrain must be projected.")

        if parameters[4].value is True and parameters[5].value is None:
            parameters[5].setErrorMessage("A path to the Blender executable must be provided.")

    def blender_path(self):
        blender_cfg = os.path.join(USER_PREFS_PATH, "blender.json")
        if not os.path.exists(blender_cfg):
            return False
        else:
            with open(blender_cfg, "r") as cf:
                b = json.load(cf)
                return PureWindowsPath(b["blender_exe"])
                
    def collada_downgrade(self, path_to_blender, dae_path):
        try:
            outputs = []
            for f in Path(dae_path).rglob("*.dae"):
                blender_cmd = [path_to_blender, "-b", "-P", DAE_DOWNGRADE_SCRIPT, f]
                raw_output = subprocess.check_output(
                    blender_cmd,
                    shell=True
                )
                outputs.append(raw_output)
                arcpy.AddMessage(f"Done processing {f}.")
            return outputs
        except subprocess.CalledProcessError as error:
            arcpy.AddMessage("Blender reported the following errors. This may mean nothing but is displayed for informational purposes.")
            arcpy.AddMessage("-------------------------BEGIN BLENDER ERROR OUTPUT-------------------------")
            arcpy.AddMessage(error.output.decode())
            arcpy.AddMessage("-------------------------END OF BLENDER ERROR OUTPUT------------------------")
            return None

    def create_blender_cfg(self, path_to_exe):
        cfg_file = os.path.join(USER_PREFS_PATH, "blender.json")
        with open(cfg_file, "w") as blender_cfg_out:
            blender_cfg_out.write(json.dumps({"blender_exe": str(PureWindowsPath(path_to_exe))}))
        return None
        
    def get_view_extent_polygon(self, sr):
        p = arcpy.mp.ArcGISProject("CURRENT")
        return p.activeView.camera.getExtent().polygon.projectAs(sr)
    
    def get_home_path(self):
        p = arcpy.mp.ArcGISProject("CURRENT")
        return Path(p.homeFolder).resolve()
    
    def now(self):
        return datetime.now().strftime("%Y%m%dT%H%M%S")
    
    def execute(self, parameters, messages):
        
        # Environments
        arcpy.env.overwriteOutput = True
        scratch = arcpy.env.scratchGDB

        # Get the Blender configuration stuff out of the way first
        if parameters[4].value:
            # We are going to add or update a Blender config file
            blender_path = self.create_blender_cfg(str(Path(parameters[5].valueAsText)))

        else:
            """
            We'll check for a Blender config file and use it if it's there,
            otherwise blender_path will be false and we'll deal with it at
            the end.
            """
            blender_path = self.blender_path()

        
        # Do the work
        try:
            img_in = parameters[0].valueAsText
            terrain_in = parameters[1].valueAsText
            out_folder_name = parameters[2].valueAsText
            
            processing_sr = arcpy.Describe(img_in).spatialReference
            extent_poly = self.get_view_extent_polygon(processing_sr)
            processing_area = extent_poly.area
            
            if processing_area <= 50000:
                rows = 1
                cols = 1
            elif processing_area > 50000 and processing_area <= 100000:
                rows = 2
                cols = 2
            elif processing_area > 100000 and processing_area <= 150000:
                rows = 3
                cols = 3
            elif processing_area > 150000:
                rows = 4
                cols = 4
                
            q = parameters[3].valueAsText
            if q == "Low":
                z = 2
            elif q == "Medium":
                z = 1
            elif q == "High":
                z = .5
            elif q == "Insane":
                z = .1
                
            folder_out = os.path.join(self.get_home_path(), f"3D/{out_folder_name}")
            
            if not os.path.exists(folder_out):
                os.makedirs(folder_out)
            
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
            tin = arcpy.CreateTin_3d(
                tin_name,
                spatial_reference=processing_sr,
                in_features=tin_params,
                constrained_delaunay="DELAUNAY")

            # Convert flat TIN to flat multipatch
            fm_name = os.path.join(scratch, "flat_mp")
            arcpy.InterpolatePolyToPatch_3d(tin, mask, fm_name, "", "1", "Area", "SArea", "0")
            
            # Convert flat multipatch to flat collada
            flat_dae_name = os.path.join(folder_out, "flat")
            arcpy.MultipatchToCollada_conversion(fm_name, flat_dae_name, "PREPEND_SOURCE_NAME", "")
            
            # Create fishnet terrain tiles
            arcpy.SetProgressor("default", "creating Collada terrain...")
            fn_name = os.path.join(scratch, "fishnet")
            view_desc = arcpy.Describe(mask)
            origin_coord = str(view_desc.extent.lowerLeft)
            view_xmin = view_desc.extent.XMin
            view_ymax = view_desc.extent.YMax
            y_axis_coord = f"{str(view_xmin)} {str(view_ymax + 10)}"
            
            arcpy.CreateFishnet_management(
                fn_name,
                origin_coord,
                y_axis_coord,
                "0",
                "0",
                rows,
                cols,
                "",
                "NO_LABELS",
                mask,
                "POLYGON"
            )
            
            # Convert extracted terrain to TIN
            rtin_name = os.path.join(folder_out, "TIN")
            arcpy.RasterTin_3d(terrain_xtract, rtin_name, z, "", "1")
            
            # Convert TIN to Multipatch
            fn_mp_name = os.path.join(scratch, "fnmp")
            arcpy.InterpolatePolyToPatch_3d(rtin_name, fn_name, fn_mp_name, "", "1", "Area", "SArea", "0")
            
            # Convert multipatch to Collada
            terr_dae_name = os.path.join(folder_out, "terrain")
            arcpy.MultipatchToCollada_conversion(fn_mp_name, terr_dae_name, "PREPEND_NONE", "")
            
            # Merge Collada tiles
            full_terr_mp_name = os.path.join(scratch, "ftmp")
            arcpy.InterpolatePolyToPatch_3d(rtin_name, mask, full_terr_mp_name, "", "1", "Area", "SArea", "0")
            full_terr_dae_name = os.path.join(folder_out, "Full")
            arcpy.MultipatchToCollada_conversion(full_terr_mp_name, full_terr_dae_name, "PREPEND_SOURCE_NAME", "")
            
            # Return licenses
            arcpy.CheckInExtension("Spatial")
            arcpy.CheckInExtension("3D")
            
            # Do Blender Collada conversion if Blender's available
            if blender_path:
                for fp in [full_terr_dae_name, flat_dae_name]:
                    arcpy.AddMessage(f"Attempting to convert content in {fp} to Collada 1.4...")
                    self.collada_downgrade(blender_path, fp)
            
            arcpy.AddMessage("Completed processing.")
        except arcpy.ExecuteError:
            arcpy.AddWarning(arcpy.GetMessages())
            raise arcpy.ExecuteError

