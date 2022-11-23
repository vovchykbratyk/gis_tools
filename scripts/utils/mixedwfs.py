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
