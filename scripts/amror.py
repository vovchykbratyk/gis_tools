"""
Area Max Rise Over Run (AMROR) brings efficiency to artillery units by enabling them
to provide a general deployment area, a firing distance, and an azimuth.  The tool takes
a surface raster, a terrain (bare earth) raster and user parameters to provide a gridded
raster with maximum inclination values expressed in mils.

Credits:
M. Ekegren @ CRREL; E. Eagle @ INSCOM
"""
import arcpy

arcpy.CheckOutExtension('Spatial')
from arcpy.sa import *
from collections import defaultdict
import json
from math import *
import os
import sys

sys.dont_write_bytecode = True


class AreaMaxRiseOverRun(object):

    def __init__(self):
        self.category = 'Analysis'
        self.name = 'AreaMaximumRiseOverRun'
        self.label = 'Area Maximum Rise Over Run'
        self.alias = 'Calculate Max Rise Over Run'
        self.description = 'Calculate maximum angle of inclination by azimuth and distance'
        self.canRunInBackground = False

    def getParameterInfo(self):
        
        pdata = [
            ['Area of Operations', 'area_of_operations', 'GPString', 'Required', 'Input'],
            ['AO Layer', 'ao_layer', 'GPFeatureLayer', 'Optional', 'Input'],
            ['Surface Raster (DSM)', 'surface_raster', 'GPRasterLayer', 'Required', 'Input'],
            ['Bare Earth Raster (DTM)', 'terrain_raster', 'GPRasterLayer', 'Required', 'Input'],
            ['Cell Size (meters)', 'cell_size', 'GPLong', 'Required', 'Input'],
            ['Distance (meters)', 'distance', 'GPLong', 'Required', 'Input'],
            ['Bearing (degrees)', 'bearing', 'GPLong', 'Required', 'Input'],
            ['Interval (meters)', 'interval', 'GPLong', 'Required', 'Input'],
            ['Vertical Offset (meters)', 'vertical_offset', 'GPLong', 'Required', 'Input'],
            ['Raster Output', 'raster_output', 'DERasterDataset', 'Optional', 'Output']
        ]

        params = [
            arcpy.Parameter(
                displayName=d[0],
                name=d[1],
                datatype=d[2],
                parameterType=d[3],
                direction=d[4]) for d in [p for p in pdata]]

        # Presets/Defaults
        params[0].filter.type = 'ValueList'
        params[0].filter.list = ['By Polygon', 'By View Extent']
        params[0].value = 'By View Extent'

        params[1].filter.list = ['Polygon']
        params[4].value = 25  # Default cell size
        params[5].value = 1000  # Default distance
        params[7].value = 20  # Default interval
        params[8].value = 2  # Default vertical offset

        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        if parameters[0].valueAsText == 'By View Extent':
            parameters[1].enabled = False
            for p in parameters[2:]:
                p.enabled = True
        else:
            for p in parameters[1:]:
                p.enabled = True
        return True

    def updateMessages(self, parameters):
        return True

    def get_view_extent(self):
        p = arcpy.mp.ArcGISProject('CURRENT')
        ext = p.activeView.camera.getExtent()
        ll = ext.lowerLeft
        ur = ext.upperRight
        return Extent(ll.X, ll.Y, ur.X, ur.Y)

    def copy_sample_values(self, source_lyr, target_lyr, target_field):
        """
        Method to avoid costly joins.  Extract join key and sample values to dict,
        then use a da.UpdateCursor() to update target point feature class with
        sampled raster values.
        """
        sample_vals = dict([(r[2], r[-1]) for r in arcpy.da.SearchCursor(source_lyr, '*')])
        with arcpy.da.UpdateCursor(target_lyr, ['OID@', target_field]) as update_rows:
            for row in update_rows:
                row[1] = sample_vals[row[0]]
                update_rows.updateRow(row)
        del update_rows
        return True

    def curvature(self, sample_distance: int):
        return 0.2032 * ((sample_distance / 1609) ** 2)

    def calc_degs(self, dtm, dsm, distance, curvature, vo):
        return atan(((dsm - curvature) - (dtm + vo)) / distance) * (180 / pi)

    def get_name(self, path):
        return os.path.splitext(os.path.split(path)[1])[0]

    def deg_to_valid_mils(self, degs):
        m = degs * (6400 / 360)
        if (m > 1600) or (m < -1600):
            return None
        else:
            return m

    def execute(self, parameters, messages):
        # Environments
        arcpy.env.overwriteOutput = True
        p = arcpy.mp.ArcGISProject('CURRENT')
        default_db = p.defaultGeodatabase
        scratch = arcpy.env.scratchGDB
        
        # Parameters
        cellsize = parameters[4].value
        distance = parameters[5].value
        bearing = parameters[6].value
        interval = parameters[7].value
        vert_offset = parameters[8].value
        
        dsm = parameters[2].valueAsText
        dtm = parameters[3].valueAsText

        # Get spatial reference from input surface raster
        sr = arcpy.Describe(dsm).spatialReference
        arcpy.env.outputCoordinateSystem = sr

        ao_selection = parameters[0].valueAsText
        
        if ao_selection == 'By View Extent':
            ao_extent = self.get_view_extent()
            arcpy.AddMessage(f'Using view extent: {ao_extent}')
        else:
            poly_lyr = parameters[1].valueAsText
            ao_poly = arcpy.Describe(poly_lyr).extent
            ao_extent = Extent(ao_poly.XMin, ao_poly.YMin, ao_poly.XMax, ao_poly.YMax)
            arcpy.AddMessage(f'Using {poly_lyr} extent: {ao_extent}')

        # Generate fishnet and get center points
        arcpy.SetProgressor('default', 'Generating sample points over deployment area...')
        arcpy.CreateFishnet_management(
            r'memory\fn',
            f'{ao_extent.XMin} {ao_extent.YMin}',
            f'{ao_extent.XMin} {ao_extent.YMax}',
            cellsize,
            cellsize,
            corner_coord=f'{ao_extent.XMax} {ao_extent.YMax}'
        )

        ao_cell_centers = r'memory\fn_label'
        arcpy.AddFields_management(
            ao_cell_centers,
            [['distance', 'LONG'],
             ['bearing', 'LONG']]
        )

        # dtm_sampled will be the final table from which we will build the raster
        arcpy.SetProgressor('default', 'Sampling bare earth dataset...')
        dtm_sampled = Sample(
            dtm,
            ao_cell_centers,
            r'memory\dtm_samp',
            unique_id_field='OID',
            generate_feature_class='FEATURE_CLASS'
        )
        
        # Add the fields required to dtm_sampled
        arcpy.AddFields_management(
            dtm_sampled,
            [['incline_deg', 'DOUBLE'],
             ['incline_mil', 'DOUBLE']]
        )
        
        """
        dtm_sampled row now looks like:
        
        (OID, (SHAPE@XY), LOCATIONID, X, Y, <dtm name>, incline_deg, incline_mil)
        """

        arcpy.SetProgressor('default', 'Updating fields...')
        with arcpy.da.UpdateCursor(ao_cell_centers, ['distance', 'bearing']) as cursor:
            for row in cursor:
                row[0] = distance
                row[1] = bearing
                cursor.updateRow(row)
        del cursor

        arcpy.AddXY_management(ao_cell_centers)

        # Now construct lines of bearing from the table
        # Switch location to os.path.join(scratch, 'az_lines') for debugging or memory failure
        arcpy.SetProgressor('default', 'Building lines of bearing...')
        az_lines = arcpy.BearingDistanceToLine_management(
            ao_cell_centers,
            r'memory\az_lines',
            'POINT_X',
            'POINT_Y',
            distance_field='distance',
            distance_units='METERS',
            bearing_field='bearing',
            spatial_reference=sr
        )

        """
        Lines of bearing row should now look like this:

        (OID, (SHAPE@), LOCATIONID, X, Y, <dsm name>, distance, bearing, ORIG_FID, Shape_Length)
        """

        # Build points along line at fixed intervals
        # Switch output to os.path.join(scratch, 'samplepoints') for debugging or memory failure
        arcpy.SetProgressor('default', 'Creating sample points along lines...')
        samplepoints = arcpy.GeneratePointsAlongLines_management(
            az_lines,
            os.path.join(scratch, 'samplepoints'),
            'DISTANCE',
            Distance=f'{interval} meters',
            Include_End_Points='END_POINTS'
        )
        arcpy.AddXY_management(samplepoints)

        # Sample the DSM
        arcpy.SetProgressor('default', 'Sampling surface dataset...')
        # Switch output to os.path.join(scratch, 'dsm_sam') for debugging or memory failure
        dsm_sampled = Sample(dsm, samplepoints, os.path.join(scratch, 'dsm_sam'),
                             generate_feature_class='FEATURE_CLASS')

        # Add from_origin, dsm, and curvature to samplepoints
        arcpy.SetProgressor('default', 'Adding analysis fields to sampled points...')
        arcpy.AddFields_management(
            samplepoints,
            [['from_origin', 'FLOAT'],
             ['dsm', 'FLOAT'],
             ['curvature', 'DOUBLE']])

        """
        Update each point's distance from origin as a member of its ORIG_FID group.
        This will be used to calculate curvature value.
        
        Copy over the DSM sample values to samplepoints.
        """
        c = defaultdict(list)
        arcpy.SetProgressor('default', "Calculating each point's curvature and distance from origin...")
        with arcpy.da.SearchCursor(samplepoints, ['OID@', 'ORIG_FID', 'from_origin']) as sc:
            for row in sc:
                c[row[1]].append(row)
        c = json.loads(json.dumps(c))
        del sc

        # Calculate distance to origin for each point grouped by ORIG_FID
        sp_with_intervals = {int(k): [(a, b, interval * i) for i, (a, b, c) in enumerate(v)] for k, v in c.items()}
        
        with arcpy.da.UpdateCursor(samplepoints, ['OID@', 'ORIG_FID', 'from_origin', 'curvature']) as uc:
            for u_row in uc:
                if u_row[1] in sp_with_intervals.keys():
                    for n_row in sp_with_intervals[u_row[1]]:
                        if n_row[0] == u_row[0]:  # Check OID alignment
                            u_row[2] = n_row[2]
                            u_row[3] = self.curvature(sample_distance=u_row[2])
                uc.updateRow(u_row)
        del uc
        
        # Copy over DSM sampled values to samplepoints
        self.copy_sample_values(dsm_sampled, samplepoints, 'dsm')

        """
        Row in samplepoints now looks like:

        (OID, (SHAPE@XY), ORIG_FID, POINT_X, POINT_Y, DISTANCE, BEARING, SHAPE_LENGTH, FROM_ORIGIN, DSM, CURVATURE)
        """
        
        # Calculate the inclination of each point between the dtm_sampled (origin) and samplepoints
        # Set up the cursors

        s = defaultdict(list)
        
        with arcpy.da.SearchCursor(samplepoints, ['ORIG_FID', 'from_origin', 'dsm', 'curvature']) as sp_cursor:
            for row in sp_cursor:
                s[row[0]].append(row)
        del sp_cursor

        samps = dict((k, [i for i in v if i[1] > 0]) for k, v in s.items())

        with arcpy.da.UpdateCursor(dtm_sampled, '*') as dtm_cursor:
            for row in dtm_cursor:
                loc_id = row[2]
                dtm_val = row[5]
                if loc_id in samps.keys():
                    i = []
                    s_points = samps[loc_id]
                    for sp in s_points:
                        d = sp[1]
                        c = sp[3]
                        dsm_val = sp[2]
                        try:
                            inclination = self.calc_degs(dtm_val, dsm_val, d, c, vert_offset)
                            i.append(inclination)
                        except TypeError:  # This covers distances not covered by surface raster
                            i.append(-9999)
                    max_inclination = max(i)
                    row[6] = max_inclination
                    row[7] = self.deg_to_valid_mils(max_inclination)
                dtm_cursor.updateRow(row)
        del dtm_cursor

        # Now create the final output raster from the points based on inclination
        arcpy.SetProgressor('default', 'Writing out inclination raster...')
        
        if parameters[9].valueAsText:
            out_raster = parameters[9].valueAsText
        else:
            out_raster = os.path.join(default_db, arcpy.CreateScratchName(
                prefix=f'Incl_{bearing}_',
                suffix='',
                data_type='RasterDataset'))

        incl_raster = arcpy.PointToRaster_conversion(
            dtm_sampled,
            'incline_mil',
            out_raster,
            cell_assigment='MEAN',
            cellsize=cellsize
        )
        
        return incl_raster
