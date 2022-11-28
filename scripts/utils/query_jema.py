import arcpy
import json
import os
from pathlib import Path
from uuid import uuid4

from arcpki import ArcPKI

CFG_DIR = os.path.join(Path(os.path.dirname(__file__)).parent, "cfg")
JEMA_CONFIG_FILE = os.path.join(CFG_DIR, "jema_config.json")


class JEMA:
  
  def __init__(self):
      """
      Sets up a session to do a GET call to the JEMA open source photo search model
      """
      self.cfg = self.jema_cfg()
      self.root = self.cfg["root"]
      self.model_id = self.cfg["model_id"]
      self.paramset = self.cfg["input_parameter_set"]
      self.temp = self.cfg["usr_temp_path"]
      if not os.path.exists(self.temp):
          try:
              os.makedirs(self.temp)
          except PermissionError:
              self.temp = "U:/"  # Profile fallback
              
  def jema_cfg(self):
      with open(JEMA_CONFIG_FILE, "r") as cf:
          return json.load(cf)
