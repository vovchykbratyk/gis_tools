import arcpy
from arcpy.sa import *
import numpy as np
import os
import sys

sys.dont_write_bytecode = True


class CHM(object):

    def __init__(self):
        """
        Derives canopy height model (CHM) from two rasters (current)
        or point cloud (TBD) data.
        """
        self.category = 'Analysis'
        self.name = 'CHM'
        self.label = 'Calculate Canopy Height Model'
        self.alias = 'Calculate Canopy Height Model'
        self.description = 'Calculate canopy height model from two terrain data sources.'
        self.canRunInBackground = False

    def getParameterInfo(self):

        pdata = [
            ['Surface Model (DSM)', 'surface_model', ['DERasterDataset', 'GPRasterLayer'], 'Required', 'Input', None],
            ['Bare Earth Model (DTM)', 'bare_earth_model', ['DERasterDataset', 'GPRasterLayer'], 'Required', 'Input', None],
            ['Output Name', 'output_name', 'GPString', 'Optional', 'Input', None],
            ['Run in memory?', 'run_in_memory', 'GPBoolean', 'Required', 'Input', 'Advanced Options']
        ]

        params = [
            arcpy.Parameter(
                displayName=d[0], 
                name=d[1], 
                datatype=d[2], 
                parameterType=d[3], 
                direction=d[4],
                category=d[5]) for d in [p for p in pdata]]
        
        params[3].value = True
        
        return params
    
    def isLicensed(self):
        return True
    
    def updateParameters(self, parameters):
        return True
    
    def updateMessages(self, parameters):
        return True
    
    def subtract_array(self, array1, array2):
        return array1 - array2
    
    def execute(self, parameters, messages):
        arcpy.CheckOutExtension('Spatial')
        arcpy.env.overwriteOutput = True

        p = arcpy.mp.ArcGISProject('CURRENT')
        db = p.defaultGeodatabase
        m = p.activeMap

        dsm = parameters[0].valueAsText
        r = arcpy.Raster(dsm)
        cell_size_x = r.meanCellWidth
        cell_size_y = r.meanCellHeight

        dsm_ll = arcpy.Describe(dsm).Extent.lowerLeft
        dtm = parameters[1].valueAsText
        out_raster = os.path.join(db, parameters[2].valueAsText)
        mem = parameters[3].value

        if mem:
            # Use numpy arrays for great speed...
            arcpy.env.outputCoordinateSystem = dsm
            arcpy.SetProgressor('default', 'Converting rasters to arrays...')
            dsm_arr = arcpy.RasterToNumPyArray(dsm, nodata_to_value=0)
            dtm_arr = arcpy.RasterToNumPyArray(dtm, nodata_to_value=0)
            arcpy.SetProgressor('default', 'Doing math...')
            diff_arr = dsm_arr - dtm_arr
            diff_arr[np.where(diff_arr < 1.8)] = 0
            diff = arcpy.NumPyArrayToRaster(
                diff_arr,
                dsm_ll,
                cell_size_x,
                cell_size_y,
                value_to_nodata=0)
            diff.save(out_raster)
        else:
            # ...or raster calculator for great stability
            arcpy.SetProgressor('default', 'Doing raster math...')
            diff_calc = RasterCalculator([dsm, dtm], ['surface', 'bare'], 'surface-bare')
            arcpy.SetProgressor('default', 'Setting null values...')
            diff = SetNull(diff_calc, diff_calc, 'Value < 1.8')
            diff.save(out_raster)

        chm_lyr = m.addDataFromPath(out_raster)
        sym = chm_lyr.symbology
        sym.updateColorizer('RasterClassifyColorizer')
        sym.colorizer.classificationField = 'Value'
        sym.colorizer.breakCount = 16
        sym.colorizer.colorRamp = p.listColorRamps('Condition Number')[0]
        sym.colorizer.noDataColor = {'RGB': [0, 0, 0, 0]}
        chm_lyr.symbology = sym
