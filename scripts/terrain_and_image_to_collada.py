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
            displayName="Processing Area",
            name="processing_area",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        param0.filter.type = "ValueList"
        param0.filter.list = ["By View Extent", "By Polygon Layer"]
        param0.value = "By View Extent"

        param1 = arcpy.Parameter(
            displayName="Polygon Layer",
            name="poly_layer",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input"
        )
        param1.filter.list = ["Polygon"]

        param2 = arcpy.Parameter(
            displayName="Image Layer",
            name="img_in",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input"
        )
        
        param3 = arcpy.Parameter(
            displayName="Terrain Layer",
            name="terrain_in",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input"
        ) 
        
        param4 = arcpy.Parameter(
            displayName="Output Folder Name",
            name="folderout",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        
        param5 = arcpy.Parameter(
            category="Advanced Options",
            displayName="Quality",
            name="quality",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
        )                
        
        param5.filter.type = "ValueList"
        param5.filter.list = [
            "Low (Z Sensitivity: 2)",
            "Medium (Z Sensitivity: 1) [DEFAULT]",
            "High (Z Sensitivity: .5)",
            "Insane (Z Sensitivity: .1)"
        ]
        param5.value = "Medium (Z Sensitivity: 1) [DEFAULT]"
        
        return [param0, param1, param2, param3, param4, param5]
     
    def isLicensed(self):
        return True
    
    def updateParameters(self, parameters):
        if parameters[0].valueAsText == "By Polygon Layer":
            parameters[1].enabled = True
        else:
            parameters[1].enabled = False

        return True
    
    def updateMessages(self, parameters):
        # Check if both layers are projected and if they match
        if parameters[0].altered:
            if parameters[0].valueAsText == "By Polygon Layer":
                if parameters[1].value is None:
                    parameters[1].setErrorMessage("Provide a polygon layer for processing.")
        if parameters[2].altered:
            img_in_sr = arcpy.Describe(parameters[2].valueAsText).spatialReference
            
            if img_in_sr.type == "Geographic":
                parameters[2].setErrorMessage("Input image must be projected.")
                
            if parameters[3].altered:
                terr_in_sr = arcpy.Describe(parameters[3].valueAsText).spatialReference
                if terr_in_sr.factoryCode != img_in_sr.factoryCode:
                    if terr_in_sr.type != "Geographic":  # Only checking for different projections here
                        parameters[3].setErrorMessage(f"Input terrain projection (EPSG:{terr_in_sr.factoryCode}) does not match input image (EPSG:{img_in_sr.factoryCode})")
        
        if parameters[3].altered:
            terr_in_sr = arcpy.Describe(parameters[3].valueAsText).spatialReference
            if terr_in_sr.type == "Geographic":
                parameters[3].setErrorMessage("Input terrain must be projected.")
                
        return
        
    def get_view_extent_polygon(self, sr):
        p = arcpy.mp.ArcGISProject("CURRENT")
        return p.activeView.camera.getExtent().polygon.projectAs(sr)
    
    def get_home_path(self):
        p = arcpy.mp.ArcGISProject("CURRENT")
        return Path(p.homeFolder).resolve()
    
    def now(self):
        return datetime.now().strftime("%Y%m%dT%H%M%S")

    def set_rows_and_cols(self, area):
        if area <= 50000:
            return 2, 2
        elif area > 50000 and area <= 100000:
            return 3, 3
        elif area > 100000 and area <= 150000:
            return 4, 4
        elif area > 150000:
            return 6, 6

    def set_z_sensitivity(self, sensitivity: str):
        if sensitivity == "Low (Z Sensitivity: 2)":
            return 2
        elif sensitivity == "Medium (Z Sensitivity: 1) [DEFAULT]":
            return 1
        elif sensitivity == "High (Z Sensitivity: .5)":
            return .5
        elif sensitivity == "Insane (Z Sensitivity: .1)":
            return .1

    def to_collada(self, mask, image_layer, terrain_layer, rows, cols, z_sensitivity, spatial_ref, folder_out):
        # Write to scratchGDB. In future we need to move to memory
        scratch = arcpy.env.scratchGDB

        arcpy.SetProgressor("default", "Setting job extent...")
        img_lyr = arcpy.MakeRasterLayer_management(image)
        terrain_lyr = arcpy.MakeRasterLayer_management(terrain)
        
        img_xtract_raw = ExtractByMask(img_lyr, mask)
        img_xtract = arcpy.ia.ExtractBand(img_xtract_raw, [1, 2, 3])
        terrain_xtract = ExtractByMask(terrain_lyr, mask)
        
        # Convert image to JPEG for painting Collada model
        jpg_out = os.path.join(folder_out, "paint.jpg")
        arcpy.CopyRaster_management(
            img_xtract, jpg_out,
            nodata_value="255",
            pixel_type="8_BIT_UNSIGNED",
            RGB_to_Colormap="NONE")

        # Create single flat .dae for digitizing
        arcpy.SetProgressor("default", "Creating Collada (Flat)...")
        tin_params = f"{mask} Shape_Area Soft_Clip"
        tin_name = os.path.join(folder_out, "TIN", "Flat")
        if not os.path.exists(tin_name): os.makedirs(tin_name)
        flat_tin = arcpy.CreateTin_3d(
            tin_name,
            spatial_reference=spatial_ref,
            in_features=tin_params,
            constrained_delaunay="DELAUNAY")

        # Convert flat TIN to flat multipatch
        flat_mp_name = os.path.join(scratch, "flat_mp")
        arcpy.InterpolatePolyToPatch_3d(flat_tin, mask, flat_mp_name, "", "1", "Area", "SArea", "0")

        # Convert flat multipatch to flat Collada
        flat_dae_name = os.path.join(folder_out, "Flat")
        arcpy.MultipatchToCollada_conversion(flat_mp_name, flat_dae_name, "PREPEND_SOURCE_NAME", "", collada_version="1.4")

        # Create fishnet terrain tiles
        arcpy.SetProgressor("default", "Creating Collada (Terrain)...")
        fishnet = os.path.join(scratch, "fishnet")
        view_desc = arcpy.Describe(mask)
        origin_coord = str(view_desc.extent.lowerLeft)
        view_xmin = view_desc.extent.XMin
        view_ymax = view_desc.extent.YMax
        y_axis_coord = f"{str(view_xmin)} {str(view_ymax + 10)}"

        arcpy.CreateFishnet_management(
            fishnet,
            origin_coord,
            y_axis_coord,
            "0",
            "0",
            rows,
            cols,
            "",
            "NO_LABELS",
            mask,
            "POLYGON")

        # Convert extracted terrain to TIN
        rtin_name = os.path.join(folder_out, "TIN", "Terrain")
        arcpy.RasterTin_3d(terrain_xtract, rtin_name, z, "", "1")

        # Convert terrain TIN to multipatch
        terrain_mp_name = os.path.join(scratch, "terrainmp")
        arcpy.InterpolatePolyToPatch_3d(rtin_name, fishnet, terrain_mp_name, "", "1", "Area", "SArea", "0")

        # Convert terrain multipatch to Collada
        terr_dae_name = os.path.join(folder_out, "Terrain")
        arcpy.MultipatchToCollada_conversion(terrain_mp_name, terr_dae_name, "PREPEND_NONE", "", collada_version="1.4")

        # Merge Collada tiles (if necessary)
        full_terr_mp_name = os.path.join(scratch, "terrainfullmp")
        arcpy.InterpolatePolyToPatch_3d(rtin_name, mask, full_terr_mp_name, "", "1", "Area", "SArea", "0")
        full_terr_dae_name = os.path.join(folder_out, "Full")
        arcpy.MultipatchToCollada_conversion(full_terr_mp_name, full_terr_dae_name, "PREPEND_SOURCE_NAME", "", collada_version="1.4")

        return flat_dae_name, full_terr_dae_name

    def execute(self, parameters, messages):
        
        # Environments
        arcpy.env.overwriteOutput = True
        scratch = arcpy.env.scratchGDB
        
        # Do the work
        try:
            img_in = parameters[2].valueAsText
            terrain_in = parameters[3].valueAsText
            out_folder = os.path.join(self.get_home_path(), "3D", parameters[4].valueAsText)
            if not os.path.exists(out_folder): os.makedirs(out_folder)
            processing_sr = arcpy.Describe(img_in).spatialReference
            z_sensitivity = self.set_z_sensitivity(parameters[5].valueAsText)

            if parameters[0].valueAsText == "By Polygon Layer":
                # Iterate over the polygon layer and kick off jobs for each feature
                feature_count = arcpy.GetCount_management(parameters[1].valueAsText)
                with arcpy.da.SearchCursor(parameters[1].valueAsText, ["SHAPE@", "OID@"]) as cursor:
                    for row in cursor:
                        geom, oid = row
                        geom = geom.projectAs(processing_sr)
                        arcpy.AddMessage(f"Processing feature {oid + 1} of {feature_count}.")
                        # Testing fishnetted processing on very high quality requests | 2023-08-18 | E. Eagle
                        if z_sensitivity < 1:
                            rows, cols = 6, 6  # For very dense posts even over a limited area we break it into chunks
                        else:
                            rows, cols = self.set_rows_and_cols(geom.area)
                        if oid < 10: oid = f"0{oid}"
                        job_out_path = os.path.join(out_folder, f"AOI_{oid}")
                        if not os.path.exists(job_out_path): os.makedirs(job_out_path)
                        mask = arcpy.CopyFeatures_management(geom, os.path.join(scratch, mask))
                        converted = self.to_collada(
                            mask,
                            img_in,
                            terrain_in,
                            rows,
                            cols,
                            z_sensitivity,
                            processing_sr, 
                            job_out_path)
                        arcpy.AddMessage(f"Finished processing feature {oid}.")
                        arcpy.AddMessage(f"\tFlat Collada may be found at {converted[0]}")
                        arcpy.AddMessage(f"\tTerrain Collada may be found at {converted[1]}")
                        arcpy.AddMessage("--------------------------------------------------------------------")
            else:
                # We're running by view extent, so only one job will be executed.
                arcpy.AddMessage("Processing view extent...")
                extent_poly = self.get_view_extent_polygon(processing_sr)
                rows, cols = self.set_rows_and_cols(extent_poly.area)
                mask = arcpy.CopyFeatures_management(extent_poly, os.path.join(scratch, "mask"))
                converted = self.to_collada(
                    mask,
                    img_in,
                    terrain_in,
                    rows,
                    cols,
                    z_sensitivity,
                    processing_sr,
                    out_folder)
                arcpy.AddMesssage("Finished processing view extent.")
                arcpy.AddMessage(f"\tFlat Collada may be found at {converted[0]}")
                arcpy.AddMessage(f"\tTerrain Collada may be found at {converted[1]}")
                arcpy.AddMessage("--------------------------------------------------------------------")
            
            # Return licenses
            arcpy.CheckInExtension("Spatial")
            arcpy.CheckInExtension("3D")
            arcpy.AddMessage("Completed processing.")

        except arcpy.ExecuteError:
            arcpy.AddWarning(arcpy.GetMessages())
            raise arcpy.ExecuteError
