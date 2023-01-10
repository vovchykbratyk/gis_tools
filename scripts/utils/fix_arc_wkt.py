import re


class FixArcWKT:
    
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

