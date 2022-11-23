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
    return wfs_config["BASE_URL"]
