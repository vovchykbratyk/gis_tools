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

        m = arcpy.mp.ArcGISProject('CURRENT')
        db = m.defaultGeodatabase
        activemap = m.activeMap

        dsm = parameters[0].valueAsText
        r = arcpy.Raster(dsm)
        cell_size_x = r.meanCellWidth
        cell_size_y = r.meanCellHeight

        dsm_ll = arcpy.Describe(dsm).Extent.lowerLeft
        dtm = parameters[1].valueAsText
        outname = parameters[2].valueAsText
        mem = parameters[3].value

        if mem:
            # We are going to use numpy arrays to do raster math and avoid IO drag
            dsm_arr = arcpy.RasterToNumPyArray(dsm, nodata_to_value=0)
            dtm_arr = arcpy.RasterToNumPyArray(dtm, nodata_to_value=0)
            diff_arr = dsm_arr - dtm_arr
            # Reclassification
            rm = [0.0, 1.8]
            bins = [float(x) for x in range(0,900,2)]
            bins = np.array(rm + bins[2:])
            recl = np.digitize(diff_arr, bins, right=False)

            # Make it a raster and save it
            diff = arcpy.NumPyArrayToRaster(recl, dsm_ll, cell_size_x, cell_size_y, value_to_nodata=0)
            diff.save(os.path.join(db, outname))
        else:
            # Using scratchGDB to perform reclass with intermediate dataasets
            scratch = arcpy.env.scratchGDB
            diff_ras = RasterCalculator([dsm, dtm], ['surface', 'bare'], 'surface-bare')
            diff_ras_out = os.path.join(scratch, 'diff_full')
            diff_ras.save(diff_ras_out)
            # Remap values
            rm = [[-9999,1.8,'NODATA'],[1.8,4.0,1]]  # Set up the first two catch-all values
            bins = [[float(s),float(s+2),i] for i, s in enumerate(range(0,900,2))]  # Go out to around 900m at 2m increments, just in case
            rm = rm + bins[2:]
            reclassed = Reclassify(diff_ras_out, 'Value', RemapRange(rm))
            reclassed.save(os.path.join(db, outname))








