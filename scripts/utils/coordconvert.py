import arcpy
import json
import os
from pathlib import Path
import re
import sys

    
class CoordConvert:
    
    def __init__(self, coord):
        self.coord = str(coord).strip()
        spaces = 0
        for c in self.coord:
            if c.isspace():
                spaces += 1
        if spaces > 1:  # It's likely a MGRS coordinate so remove all whitespace
            self.coord = str(self.coord).replace(" ", "")
            
        self.coord_type = self._get_coord_type()
        
    def _get_coord_type(self):
        # Figure out what kind of notation we're dealing with
        mgrs_pattern = re.compile(r"^\d{1,2}[A-Z]{3}[0-9]+")
        arc_dms_pattern = re.compile(r"^\d{1,3}.{1}\d{1,2}\'\d{1,2}\"[EW]{1}\s{1}\d{1,3}.\d{1,2}\'\d{1,2}\"[NS]{1}\s?")
        dms_pattern = re.compile(r"^\d{6}(\.\d{1,3})?[NS]{1}\s?\d{6,7}(\.\d{1,3})?[EW]{1}")
        arc_dd_pattern = re.compile(r"(\d{1,3}\.\d+.[EW]?\s?\d{1,2}\.\d+.[NS]?)$")
        dd_pattern = re.compile(r"^(\d+\.\d+?[NSEW]?[,\s]{0,2}\d+\.\d+?[NSEW]?)$")
        
        patterns = {
            "MGRS": mgrs_pattern,
            "ArcGIS_Pro_DMS": arc_dms_pattern,
            "DMS": dms_pattern,
            "ArcGIS_Pro_DD": arc_dd_pattern,
            "DD": dd_pattern,
        }
        
        for k, v in patterns.items():
            if v.search(self.coord):
                #print(f"INPUT COORDS: {self.coord} | TYPE: {k}")
                return self.coord, k
            
    def to_osrm_dd(self, dd_in_standard_order=True):
        """
        Take input coordinate and notation and output decimal degree
        notation in {longitude},{latitude} string.
        """
        osrm_dd = {}
        in_type = self.coord_type[1]
        
        osrm_dd["layername"] = None
            
        if in_type == "MGRS":
            arcpy.AddMessage("Detected MGRS Coordinate...")
            p = arcpy.FromCoordString(self.coord, "MGRS")
            dd = self.to_lat_lon(p.toCoordString("DD"))
            osrm_dd["coordstring"] = f"{str(dd[1])},{str(dd[0])}"
            osrm_dd["point"] = p
            
        elif in_type == "ArcGIS_Pro_DMS":  # Comes in longitude-latitude format
            ss = r"^(\d{1,3}).{1}(\d{1,2})\'(\d{1,2}\"([EW]{1})\s{1}(\d{1,3}).(\d{1,2})\'(\d{1,2})\"([NS]{1})\s?"
            x = re.search(ss, self.coord).groups()
            llstr = []
            for i in x[:3] + x[4:7]:
                if len(i) < 2:
                    i = '0' + str(i)
                llstr.append(i)
            llstr.insert(3, x[3])
            llstr.insert(7, x[7])
            
            p = arcpy.FromCoordString(f"{' '.join(llstr[4:8])} {' '.join(llstr[:4])}", "DMS")
            dd = self.to_lat_lon(p.toCoordString("DD"))
            
            osrm_dd["coordstring"] = f"{str(dd[1])},{str(dd[0])}"
            osrm_dd["point"] = p
        
        elif in_type == "DMS":
            dms_in = self.coord.strip().replace(" ", "")
            dms_patt = r"^(\d{2})(\d{2})(\d{2}[NS])(\d{2,3})(\d{2})(\d{2}[EW])"
            parsed_dms = re.search(dms_patt, dms_in).groups()
            dms = " ".join(parsed_dms)
            p = arcpy.FromCoordString(dms, "DMS")
            dd = self.to_lat_lon(p.toCoordString("DD"))
            osrm_dd["coordstring"] = f"{str(dd[1])},{str(dd[0])}"
            osrm_dd["point"] = p
            
        elif in_type == "ArcGIS_Pro_DD":
            coords = self.coord.split(" ")
            lonlat = []
            for i in coords:
                lonlat.append(i[:-2])
            osrm_dd["coordstring"] = ",".join(lonlat)
            osrm_dd["point"] = arcpy.Point(float(lonlat[0]), float(lonlat[1]))
        
        elif in_type == "DD":
            if dd_in_standard_order:
                # Assume standard decimal degree notation is delivered in LATITUDE,LONGITUDE order.
                parsed = re.match(r"(^\d{2}\.\d+)[NS]?,?\s?(\d{2}\.\d+)[EW]?", self.coord)
                if parsed:
                    osrm_dd["coordstring"] = f"{parsed.group(2)},{parsed.group(1)}"
                    osrm_dd["point"] = arcpy.Point(float(parsed.group(2)), float(parsed.group(1)))
                else:
                    sys.exit(f"Couldn't parse {self.coord}")
            else:
                # User override for decimal degree notation delivered in LONGITUDE,LATITUDE order.
                parsed = re.match(r"(^\d{2}\.\d+)[EW]?,?\s?(\d{2}\.\d+)[NS]?", self.coord)
                if parsed:
                    osrm_dd["coordstring"] = f"{parsed.group(1)},{parsed.group(2)}"
                    osrm_dd["point"] = arcpy.Point(float(parsed.group(1)), float(parsed.group(2)))
                else:
                    sys.exit(f"Couldn't parse {self.coord}")
                
        return osrm_dd
    
    def to_lat_lon(self, c: str):
        lat, lon = c.split(" ")
        lat = float(lat.replace("N", "").replace("S", ""))
        lon = float(lon.replace("E", "").replace("W", ""))
        return lat, lon
