import arcpy
import json
import re
import sys

# Don't write cache files
sys.dont_write_bytecode = True

# Dependencies
try:
    import mgrs
except ImportError:
    arcpy.AddError("Could not find mgrs installed on this system.  Exiting...")
    sys.exit()
    
    
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
    
    def execute(self, parameters, messages):
        
        # Enironments
        arcpy.env.overwriteOutput = True
        
        in_fc = parameters[0].valueAsText
        d = arcpy.Describe(in_fc)
        fc_path = d.path
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
            with arcpy.da.UpdateCursor(in_fc, ["SHAPE@XY", "POINT_X", "POINT_Y", "MGRS"]) as cursor:
                total_count = 0
                for row in cursor:
                    wgs84point = arcpy.PointGeometry(arcpy.Point(row[0][0], row[0][1]), in_fc_srs).projectAs(out_srs)
                    wgs84point = json.loads(wgs84point.JSON)
                    point_x = float(wgs84point["x"])
                    point_y = float(wgs84point["y"])
                    m = mgrs.MGRS()
                    c = m.toMGRS(point_y, point_x)
                    row[1] = point_x
                    row[2] = point_y
                    row[3] = c
                    cursor = updateRow(row)
                    total_count += 1
                    
                arcpy.AddMessage(f"Finished processing.  Added {str(total_count)} coordinates.")
        except Exception as e:
            arcpy.AddWarning(e)
            pass
        
        edit.stopOperation()
        edit.stopEditing(True)
        
