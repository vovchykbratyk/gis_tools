import arcpy
import json
import re
import sys

# Don't write cache files
sys.dont_write_bytecode = True
    
    
class CoordsToAttributeTable(object):
    
    def __init__(self):
        
        self.category = "Conversions"
        self.name = "CoordsToAttributeTable"
        self.label = "Coordinates to Attribute Table"
        self.description = "Adds X/Y and MGRS to a point feature class attribute table"
        
    def getParameterInfo(self):
        
        param0 = arcpy.Parameter(
            displayName="Input Point FeatureClass",
            name="in_fc",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input"
        )
        param0.filter.list = ["Point"]
        
        return [param0]
    
    def isLicensed(self):
        return True
    
    def updateParameters(self, parameters):
        return True
    
    def updateMessages(self, parameters):
        return True

    def round_mgrs(self, mgrs_str):
        if len(mgrs_str) > 15:
            m = re.search(r"^(\d{1,2}\w{3})(\d+)", mgrs_str).groups()
            m_grid = m[0]
            m_coords = m[1]
            half = len(m_coords)//2
            easting, northing = m_coords[0:half], m_coords[half:]
            return f"{m_grid}{easting[:5]}{northing[:5]}"
        else:
            return mgrs_str
    
    def execute(self, parameters, messages):
        
        # Enironments
        arcpy.env.overwriteOutput = True
        
        in_fc = parameters[0].valueAsText
        d = arcpy.Describe(in_fc)
        fc_path = d.path
        in_fc_srs = d.spatialReference
        out_srs = arcpy.SpatialReference(4326)
        gdb_search = re.compile(r"(^._\.gdb).+")
        find_gdb = gdb_search.search(fc_path)
        if find_gdb:
            workspace = find_gdb.group(1)
        else:
            workspace = fc_path
            
        new_fields = [
            ["POINT_X", "FLOAT"],
            ["POINT_Y", "FLOAT"],
            ["MGRS", "TEXT"]
        ]
        
        for field in new_fields:
            try:
                arcpy.AddField_management(in_fc, field[0], field[1])
            except Exception as e:
                arcpy.AddWarning(e)
                pass
            
        edit = arcpy.da.Editor(workspace)
        edit.startEditing(False, False)
        edit.startOperation()
        
        try:
            with arcpy.da.UpdateCursor(in_fc, ["SHAPE@WKT", "SHAPE@XY", "POINT_X", "POINT_Y", "MGRS"]) as cursor:
                total_count = 0
                for row in cursor:
                    mgrs = arcpy.FromWKT(row[0], in_fc_srs).toCoordString("MGRS")
                    row[2] = row[1][0]  # POINT_X
                    row[3] = row[1][1]  # POINT_Y
                    row[4] = self.round_mgrs(mgrs)
                    cursor.updateRow(row)
                    total_count += 1
                    
                arcpy.AddMessage(f"Finished processing.  Added {str(total_count)} coordinates.")
        except Exception as e:
            arcpy.AddWarning(e)
            pass
        
        edit.stopOperation()
        edit.stopEditing(True)
        
