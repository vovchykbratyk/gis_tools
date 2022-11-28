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
        
    def query_photos(self, **kwargs):
        """
        Parameters:
        - startdate (YYYY-mm-ddTHH:MM:SSZ)
        - stopdate (same as above)
        - EITHER pointwkt OR polywkt (e.g., POINT(10 20)  )
        - pointwkt must have additional param radiuskm expressed in km (e.g., 25)
        """
        payload = []
        for k, v in kwargs.items():  # Set up parameters
            for pn, pv in self.cfg["params"].items():
                if k == pn:  # parameter names match, get the jema parameter value and build the query string
                    payload.append(f"{pv}={str(v).replace(':', '%3A').replace(' ', '%20')}")
        jema_url = f"{self.root}{self.model_id}&{self.paramset}&{'&'.join(payload)}"
        s = kwargs["session"]  # pass in the geoaxis session token for reuse
        model_r = s.get(jema_url)
        fn = os.path.join(self.temp, f"{uuid4()}.geojson")
        with open(fn, 'wb') as gj:
            gj.write(model_r.content)
        
        return fn
      
       
      
