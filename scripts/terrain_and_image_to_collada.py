import arcpy
from arcpy.sa import *
from datetime import datetime
import os
from pathlib import Path, PureWindowsPath
import sys

arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension("3D")

# Disable cache files
sys.dont_write_bytecode = True

# Globals
BLENDER_EXE = "C:/Program Files/Blender Foundation/Blender 3.2/blender.exe"
BLENDER_UTILS = os.path.join(os.path.dirname(__file__), "blender")
DAE_DOWNGRADE_SCRIPT = os.path.join(BLENDER_UTILS, "dae2dae.py")


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
        
        return [param0, param1, param2, param3]
     
    def isLicensed(self):
        return True
    
    def updateParameters(self, parameters):
        return True
    
    def updateMessages(self, parameters):
        img_in_sr = None
        terr_in_sr = None
        
        # Check if both layers are projected
        if parameters[0].altered:
            img_in_sr = self.check_projection(parameters[0].value)
            if not img_in_sr:
                parameters[0].setErrorMessage("Input image must be projected.")
        
        if parameters[1].altered:
            terr_in_sr = self.check_projection(parameters[1].value)
            if not terr_in_sr:
                parameters[1].setErrorMessage("Input terrain must be projected.")
                
        # If both layers are projected, check if they match
        if img_in_sr and terr_in_sr:
            if img_in_sr.factoryCode != terr_in_sr.factoryCode:
                parameters[0].setErrorMessage(f"Image EPSG:{img_in_sr.factoryCode} does not match terrain.")
                parameters[1].setErrorMessage(f"Terrain EPSG:{terr_in_sr.factoryCode} does not match image.")      
        return
    
    def check_projection(self, param_value):
        lyr_sr = arcpy.Describe(param_value).spatialReference
        if lyr_sr.factoryCode in [4326, 3857, None]:
            return None
        else:
            return lyr_sr
        
    def collada_downgrade(self, dae_path):
        try:
            outputs = []
            for f in Path(dae_path).rglob("*.dae"):
                blender_cmd = [BLENDER_EXE, "-b", "-P", DAE_DOWNGRADE_SCRIPT, f]
                raw_output = subprocess.check_output(
                    blender_cmd,
                    shell=True
                )
                outputs.append(raw_output)
                arcpy.AddMessage(f"Done processing {f}."})
            return outputs
        except subprocess.CalledProcessError as error:
            arcpy.AddMessage("Blender reported the following errors. This may mean nothing but is displayed for informational purposes.")
            arcpy.AddMessage("-------------------------BEGIN BLENDER ERROR OUTPUT-------------------------")
            arcpy.AddMessage(error.output)
            arcpy.AddMessage("-------------------------END OF BLENDER ERROR OUTPUT------------------------")
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
            
            mask = arcpy.CopyFeatures_management(extent_poly, os.path.join(r"in_memory", "mask"))
            
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
                    spatial_reference=processing_sr,
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
            if os.path.exists(BLENDER_EXE):
                for fp in [full_terr_dae_name, flat_dae_name]:
                    arcpy.AddMessage(f"Attempting to convert content in {fp} to Collada 1.4...")
                    self.collada_downgrade(PureWindowsPath(fp))
            
            arcpy.AddMessage("Completed processing.")
        except arcpy.ExecuteError:
            arcpy.AddWarning(arcpy.GetMessages())
            raise arcpy.ExecuteError

