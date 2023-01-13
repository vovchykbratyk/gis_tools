"""
This is just a little helper class I use to recast the almost-right Esri
WKT strings that are output from the geometry .WKT property, into the simplest
possible OGC format for passing to open source geospatial web services (e.g., OSRM,
GeoServer, etc.)  It will remove spaces, z-values if present, and simplify
unnecessarily complex forms (single polygons returned as multipolygons).

A sample usage:

with arcpy.da.SearchCursor(some-feature-class, ["SHAPE@WKT"]) as cursor:
    for row in cursor:
        real_wkt = EsriWKT2OGC(row[0]).fixed

"""

import re


class EsriWKT2OGC:
    
    def __init__(self, wkt):
        self.wkt = wkt
        self.line_pattern = r"^(\w+)?(LINESTRING)\s(\()\(?([^\)]+)(\))\)?"
        self.point_pattern = r"^(\w+)?(POINT)\s(\()([^\)]+)(\))"
        self.poly_pattern = r"^(\w+)?(POLYGON)\s\((\(\()([^\)]+)(\)\))\)"
        self.fixed = self._fix_arcgis_wkt()
        
    def _fix_arcgis_wkt(self):
        if re.search(self.line_pattern, self.wkt):
            groups = re.match(self.line_pattern, self.wkt).groups()
        elif re.search(self.point_pattern, self.wkt):
            groups = re.match(self.point_pattern, self.wkt).groups()
        elif re.search(self.poly_pattern, self.wkt):
            groups = re.match(self.poly_pattern, self.wkt).groups()
        return f"{groups[1]}{groups[2]}{self._remove_z(groups[3])}{groups[4]}"
    
    def _remove_z(self, coords):
        return ", ".join([f"{i[0]} {i[1]}" for i in [f.strip().split(" ") for f in coords.split(",")]])
