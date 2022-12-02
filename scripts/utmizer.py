"""
Purpose:
    This script automatically projects a dataset (raster or vector) to an appropriate UTM zone.
    
Limitations:
    Use common sense.  It's intended for local/regional datasets that make sense being
    projected to UTM.
    I haven't tested it against GeoPackage tables but there's no reason it won't work as ArcGIS
    does recognize them as feature classes.
    Does not work with KML.  Sorry.  Stop using KML.
"""




import arcpy
import os
from pathlib import Path
import sys

# Disable cache file writing
sys.dont_write_bytecode = True

UTMGRID = {}  # update with geojson UTM grid string containing EPSG field


class UTMizer(object):
    
    def __init__(self):
        self.category = "Conversions"
        self.name = "UTMizer"
        self.label = "UTMizer"
        self.description = "Automatically reprojects a raster or vector dataset to an appropriate UTM zone"
        self.canRunInBackground = False
        
    def getParameterInfo(self):
        
        param0 = arcpy.Parameter(
            displayName="Input Dataset",
            name="input_dataset",
            datatype=["GPFeatureLayer", "DEFeatureClass", "GPRasterLayer", "DERasterDataset"],
            parameterType="Required",
            direction="Input"
        )
        
        return [param0]
    
    def isLicensed(self):
        return True
    
    def updateParameters(self, parameters):
        return True
    
    def updateMessages(self, parameters):
        return True
    
    @staticmethod
    def make_temp_utm_fc(gj_string):
        sr = arcpy.SpatialReference(4326)
        temp_fc = arcpy.CreateFeatureclass_management(
            "memory", "utmzones", "POLYGON", spatial_reference=sr)
        arcpy.AddField_management(temp_fc, "EPSG", "TEXT")
        
        with arcpy.da.InsertCursor(temp_fc, ["SHAPE@", "EPSG"]) as irows:
            for feature in gj_string["features"]:
                geom = arcpy.AsShape(feature["geometry"], False)
                irows.insertRow([geom, feature["properties"]["EPSG"]])
        return temp_fc
    
    @staticmethod
    def get_extent_centroid(layer):
        for_conversion = None
        desc = arcpy.Describe(layer)
        sr = arcpy.Describe(layer).spatialReference
        gcs_sr = arcpy.SpatialReference(4326)
        
        if sr.factoryCode != 4326:  # Not in 4326, convert first
            if desc.dataType in ["FeatureLayer", "FeatureClass"]:
                temp_converted_location = "memory"
                temp_converted_name = "twgs84temp"
                for_conversion = arcpy.Project_management(
                    layer,
                    os.path.join(temp_converted_location, temp_converted_name),
                    gcs_sr
                )
            elif desc.dataType in ["RasterLayer", "RasterDataset"]:
                temp_converted_location = arcpy.env.scratchGDB
                temp_converted_name = "ToGCSTmp"
                for_conversion = arcpy.ProjectRaster_management(
                    layer,
                    os.path.join(temp_converted_location, temp_converted_name),
                    gcs_sr
                )
            else:
                arcpy.AddMessage(arcpy.GetMessages())
                raise arcpy.ExecuteError
        else:
            for_conversion = layer
            
        extent = arcpy.Describe(for_conversion).extent
        centroid = arcpy.Polygon(
            arcpy.Array(
                [
                    extent.lowerLeft,
                    extent.lowerRight,
                    extent.upperRight,
                    extent.upperLeft,
                    extent.lowerLeft
                ]
            ), spatial_reference=gcs_sr
        ).centroid
        
        return centroid
    
    def execute(self, parameters, messages):
        
        # Environments
        p = arcpy.mp.ArcGISProject("CURRENT")
        activeMap = p.activeMap
        home_folder = Path(p.homeFolder).resolve()
        d = p.defaultGeodatabase
        arcpy.env.overwriteOutput = True
        
        # Do the work
        try:
            gcs = arcpy.SpatialReference(4326)
            in_lyr = parameters[0].valueAsText
            
            arcpy.SetProgressor("default", "Initializing UTM grid...")
            utm_fc = UTMizer.make_temp_utm_fc(UTMGRID)
            
            arcpy.SetProgressor("default", "Getting layer information...")
            in_lyr_desc = arcpy.Describe(in_lyr)
            
            arcpy.SetProgressor("default", "Getting layer centroid...")
            center = UTMizer.get_extent_centroid(in_lyr)
            
            center_fc = arcpy.CreateFeatureclass_management(
                r"in_memory", "layercenter", "POINT", spatial_reference=gcs)
            
            center_row = [(center.X, center.Y)]
            arcpy.AddMessage(f"Layer centroid: {center.Y}, {center.X}")
            with arcpy.da.InsertCursor(center_fc, ["SHAPE@XY"]) as cursor:
                cursor.insertRow(center_row)
                
            arcpy.SetProgressor("default", "Running spatial join...")
            center_fc_layer = arcpy.MakeFeatureLayer_management(center_fc, "center_fc_lyr")
            utm_fc_layer = arcpy.MakeFeatureLayer_management(utm_fc, "utm_fc_lyr")
            sj = arcpy.analysis.SpatialJoin(center_fc_layer, utm_fc_layer, os.path.join(r"in_memory", "sj"))
            
            arcpy.SetProgressor("default", "Getting UTM EPSG code...")
            epsg = None
            
            with arcpy.da.SearchCursor(sj, "EPSG") as cursor:
                for row in cursor:
                    arcpy.AddMessage(f"UTM EPSG code: {row[0]}")
                    epsg = int(row[0])
                    
            arcpy.SetProgressor("default", f"Projecting layer to EPSG:{str(epsg)}...")
            if hasattr(in_lyr, "name"):
                if len(str(in_lyr.name)) > 16:
                    original_name = str(in_lyr.name[:16])
                else:
                    original_name = str(in_lyr.name)
                original_name = original_name.replace(" ", "").replace(".", "_")
                utm_out_name = ("UTM_" + original_name).replace(".", "_").replace(" ", "")
            else:
                if len(str(in_lyr_desc.file)) > 16:
                    original_name = str(in_lyr_desc.file[:16])
                else:
                    original_name = str(in_lyr_desc.file)
                original_name = original_name.replace(".", "_").replace("-", "_").replace(" ", "")
                utm_out_name = str("UTM_" + original_name).replace(".", "_").replace("-", ")").replace("__", "_")
                
            if in_lyr_desc.dataType in ["FeatureLayer", "FeatureClass"]:
                # Do vector reprojection
                utm_reproj = arcpy.Project_management(in_lyr, utm_out_name, arcpy.SpatialReference(epsg))
                arcpy.AddMessage(f"Projected {original_name} to EPSG:{epsg} (Output dataset: {utm_out_name}).")
            elif in_lyr_desc.dataType in ["RasterLayer", "RasterDataset"]:
                # Do raster reprojection
                utm_reproj = arcpy.ProjectRaster_management(in_lyr, utm_out_name, arcpy.SpatialReference(epsg))
                arcpy.AddMessage(f"Projected {original_name} to EPSG:{epsg} (Output dataset: {utm_out_name}).")
                
            out_layer = activeMap.addDataFromPath(utm_reproj)
            out_layer.name = f"{original_name}_UTM"
            
        except arcpy.ExecuteError:
            arcpy.AddMessage(arcpy.GetMessages())
            raise arcpy.ExecuteError
    
