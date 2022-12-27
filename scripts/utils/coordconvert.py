import arcpy
import json
import os
from pathlib import Path
import re
import sys

# Local imports
sys.path.append(os.path.dirname(__file__))
import arcpki
ArcPKI = arcpki.ArcPKI

# Non-Arcpy dependencies
try:
    import mgrs
except ImportError:
    arcpy.AddError("Could not find mgrs installed on this system, exiting.")
    sys.exit()
    
    
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
        self.be_url = self._get_be_url()
        
    def _get_be_url(self):
        config_file = os.path.join(Path(os.path.dirname(__file__)).parent, "cfg", "be_lookup.json")
        with open(config_file, "r") as cf:
            configs = json.load(cf)
            return configs["BE_SERVICE"]
        
    def _get_coord_type(self):
        # Figure out what kind of notation we're dealing with
        mgrs_pattern = re.compile(r"^\d{1,2}[A-Z]{3}[0-9]+")
        arc_dms_pattern = re.compile(r"^\d{1,3}.{1}\d{1,2}\'\d{1,2}\"[EW]{1}\s{1}\d{1,3}.\d{1,2}\'\d{1,2}\"[NS]{1}\s?")
        dms_pattern = re.compile(r"^\d{6}(\.\d{1,3})?[NS]{1}\s?\d{6,7}(\.\d{1,3})?[EW]{1}")
        arc_dd_pattern = re.compile(r"(\d{2,3}\.\d+.[EW]?\s?\d{2}\.\d+.[NS]?)$")
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
        
        Uses ArcPKI for calls to BE lookup
        """
        osrm_dd = {}
        in_type = self.coord_type[1]
        if in_type != "BENUM":
            osrm_dd["layername"] = None
            
            if in_type == "MGRS":
                m = mgrs.MGRS()
                d = m.toLatLon(self.coord)
                osrm_dd["coordstring"] = f"{str(d[1])},{str(d[0])}"
                osrm_dd["point"] = arcpy.Point(float(d[1]), float(d[0]))
        
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
                m = mgrs.MGRS()
                lon = m.dmstodd(''.join(llstr[:4]))
                lat = m.dmstodd(''.join(llstr[4:8]))
                osrm_dd["coordstring"] = f"{str(lon)},{str(lat)}"
                osrm_dd["point"] = arcpy.Point(float(lon), float(lat))
                
            elif in_type == "DMS":
                pattern = re.compile(r'[\W_]+')
                fixed = pattern.sub('', self.coord)
                m = mgrs.MGRS()
                lat = m.dmstodd(fixed[:7])
                lon = m.dmstodd(fixed[7:])
                osrm_dd["coordstring"] = f"{str(lon)},{str(lat)}"
                osrm_dd["point"] = arcpy.Point(float(lon), float(lat))
                
            elif in_type == "ArcGIS_Pro_DD":
                coords = self.coord.split(" ")
                lonlat = []
                for i in coords:
                    lonlat.append(i[:-2])
                osrm_dd["coordstring"] = ",".join(lonlat)
                osrm_dd["point"] = arcpy.Point(float(lonlat[0]), float(lonlat[1]))
                
            elif in_type == "DD":
                if dd_in_standard_order:
                    # Assume standard decimal degree notation is delivered in LATITUDE,LONGITUDE order
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
        else:
            raise TypeError
                
        return osrm_dd
