import arcpy
from datetime import datetime
import json
import os
from pathlib import Path
import sys

# Globals
WFS_CONFIG_FILE = os.path.join(Path(os.path.dirname(__file__)).parent, "cfg", "wfs.json")

# Local imports
sys.dont_write_bytecode = True
sys.path.append(os.path.dirname(__file__))
from arcpki import ArcPKI


def wfsconfig(config_file):
    with open(config_file, "r") as wc:
        wfs_config = json.load(wc)
    return wfs_config["GETS_URL"]


class MixedWFS:
    
    def __init__(self, params:dict, attribute_map_file=None):
        
        # Initial config
        self.now = self._now()
        self.wfs_config_file = WFS_CONFIG_FILE
        
        # Build the URL
        self.params = params
        self.payload = "&".join(
            [f"{k=v}" for k, v in self.params.items()]
        ).replace(" ", "%20").replace("'", "%27").replace("(", "%28").replace(")", "%29").replace('"', '%22')
        self.url = self.base_url() + self.payload
        arcpy.AddMessage(f"URL: {self.url}")
        self.wfs_resp = self._get_wfs_response()
        
        if attribute_map_file:
            with open(attribute_map_file, "r") as am:
                self.attmap = json.load(am)
        else:
            self.attmap = None
            
    def base_url(self):
        with open(self.wfs_config_file, "r") as wc:
            wfs_config = json.load(wc)
            return wfs_config["BASE_URL"]
        
    def _get_wfs_response(self):
        return ArcPKI().get(self.url).json()
    
    def cast(self, x, coerce=None):
        if x:
            if coerce:
                if coerce == "TEXT":
                    return str(x)
                elif coerce in ["LONG", "SHORT"]:
                    try:
                        return int(x)
                    except ValueError:
                        return 999999
                elif coerce in ["DOUBLE", "FLOAT"]:
                    try:
                        return float(x)
                    except ValueError:
                        return float(999999)
                elif coerce == "DATE":
                    try:
                        return datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ")
                    except ValueError:
                        return datetime(1900, 1, 1, 12, 0, 0)
                elif coerce == "BLOB":
                    return memoryview(str(x).encode("utf-8"))
            else:
                try:
                    return int(x)
                except ValueError:
                    try:
                        return float(x)
                    except ValueError:
                        try:
                            return datetime.strptime(x, "%Y-%m-%dT%H%H:%M:%SZ")
                        except ValueError:
                            return x
        else:
            return None
        
    def to_fc(self, out_prefix: str, json_file_output=None):
        arcpy.SetProgressor("default", "Converting mixed GeoJSON to feature classes...")
        feat_total_count = int(self.wfs_resp["totalFeatures"])
        if feat_total_count == 0:
            arcpy.AddWarning("The WFS query was successful; however, no rows were returned.  Try broadening your search dates or area.")
            sys.exit()
        feat_processed_count = 0
        feats = self.wfs_resp["features"]
        
        # Assemble the feature class creation structure
        esri_geom = {
            "point": {
                "type": "POINT",
                "token": "SHAPE@XY"
                "suffix": "P"
                "fields": [],
                "rows": []
            },
            "polyline": {
                "type": "POLYLINE",
                "token": "SHAPE@",
                "suffix": "L",
                "fields": [],
                "rows" []
            },
            "polygon": {
                "type": "POLYGON",
                "token": "SHAPE@",
                "suffix": "A",
                "fields": [],
                "rows": []
            }
        }
        
        # Populate the structure
        for feat in feats:
            geom = arcpy.AsShape(feat["geometry"])
            if geom.type in esri_geom.keys():
                atts = dict(feat["properties"])
                if self.attmap:
                    """
                    A field description document (FDD) has been provided.  Build the fields
                    based on the elements contained in the FDD.
                    """
                    for fieldname, val in atts.items():
                        for k, v in self.attmap.items():
                            if fieldname == k:
                                field_def = [fieldname] + list(v.values())
                                if field_def not in esri_geom[geom.type]["fields"]:
                                    esri_geom[geom.type]["fields"].append(field_def)
                else:
                    """
                    No FDD has been provided.  Make a good faith attempt to discern
                    data types (TEXT, DOUBLE, LONG, BLOB, etc.) by seeking through the
                    result set.
                    """
                    fields = []
                    for fieldname, value in atts.items():
                        