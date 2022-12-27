import arcpy
from datetime import datetime
import json
import os
from pathlib import Path
import requests
import sys

sys.dont_write_bytecode = True

# Globals
OSRM_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "cfg", "osrm.json")
UTILS_DIR = os.path.join(os.path.dirname(__file__), "utils")

# Local imports
sys.path.append(UTILS_DIR)
from utils import arcpki
from utils import coordconvert

ArcPKI = arcpki.ArcPKI
CoordConvert = coordconvert.CoordConvert
from utils.exceptions import ExceptionNetworkFailure


class OSRM(object):
    
    def __init__(self):
        """
        Solves simple routing in ArcGIS using an Open Source Routing Machine (OSRM) instance
        """
        self.category = "Routing"
        self.name = "OSRMRouting"
        self.label = "Route with OSRM"
        self.description = "Solve routing problems using the Open Source Routing Machine (OSRM)"
        self.canRunInBackground = False
        
    def getParameterInfo(self):
        
        param0 = arcpy.Parameter(
            displayName="Origin",
            name="startpoint",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        
        param1 = arcpy.Parameter(
            displayName="Waypoint",
            name="waypoints",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
            multiValue=True)
        
        param2 = arcpy.Parameter(
            displayName="Destination",
            name="endpoint",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        
        param3 = arcpy.Parameter(
            displayName="Reverse DD to Lon/Lat",
            name="ll_order",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        
        param4 = arcpy.Parameter(
            displayName="Get Alternate Routes",
            name="alts",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        
        return [param0, param1, param2, param3, param4]
    
    def isLicensed(self):
        return True
    
    def updateParameters(self, parameters):
        return True
    
    def updateMessages(self, parameters):
        return True
    
    def now(self):
        return datetime.now().strftime("%Y%m%dT%H%M%S")
    
    def execute(self, parameters, messages):
        
        # Environments
        p = arcpy.mp.ArcGISProject("CURRENT")
        active_map = p.activeMap
        default_db = p.defaultGeodatabase
        arcpy.env.workspace = p.defaultGeodatabase
        active_sr = active_map.spatialReference
        
        startpoint = parameters[0].valueAsText
        waypoints = parameters[1].valueAsText
        endpoint = parameters[2].valueAsText
        ll_order = parameters[3].value
        alts = paramters[4].value
        
        # Hold waypoints separately, if any
        waypoint_dict = {}
        waypoint_count = 1  # Always count waypoints starting at 1
        
        now = self.now()
        
        if ll_order:  # Decimal degrees, delivered in X/Y (Lon, Lat)
            start = CoordConvert(startpoint).to_osrm_dd(ll_order)
            end = CoordConvert(endpoint).to_osrm_dd(ll_order)
            if waypoints:
                if len(waypoints) > 9:
                    for wp in waypoints.split(";")
                    wp = wp.replace("'", "").strip()
                    wpoint = CoordConvert(wp).to_osrm_dd(ll_order)
                    if waypoint_count < 10:
                        waypoint_dict[f"waypoint_0{waypoint_count}"] = [wpoint["layername"], wpoint["coordstring"],
                                                                        wpoint["point"]]
                    else:
                        waypoint_dict[f"waypoint_{waypoint_count}"] = [wpoint["layername"], wpoint["coordstring"],
                                                                       wpoint["point"]]
                    waypoint_count += 1
        else:  # Decimal degrees, delivered in Y/X (Lat, Lon)
            start = CoordConvert(startpoint).to_osrm_dd()
            end = CoordConvert(endpoint).to_osrm_dd()
            if waypoints:
                if len(waypoints) > 0:
                    for wp in waypoints.split(";"):
                        wp = wp.replace("'", "").strip()
                        wpoint = CoordConvert(wp).to_osrm_dd()
                        if waypoint_count < 10:
                            waypoint_dict[f"waypoint_0{waypoint_count}"] = [wpoint["layername"], wpoint["coordstring"],
                                                                            wpoint["point"]]
                        else:
                            waypoint_dict[f"waypoint_{waypoint_count}"] = [wpoint["layername"], wpoint["coordstring"],
                                                                           wpoint["point"]]
                        waypoint_count += 1
                        
        origin = start["coordstring"]
        if start["layername"]:
            origin_label = start["layername"]
        else:
            origin_label = f"Origin_{now}"
            
        destination = end["coordstring"]
        if end["layername"]:
            destination_label = end["layername"]
        else:
            destination_label = f"Destination_{now}"
            
        # Set up the Origin and Destination point feature classes
        arcpy.SetProgressor("default", "Building origin and destination feature classes...")
        
        sr = arcpy.SpatialReference(4326)
        waypoint_geometry = "POINT"
        origin_fc_name = f"osrm_origin_{now}"
        origin_fc = arcpy.CreateFeatureclass_management(
            default_db, origin_fc_name, waypoint_geometry, spatial_reference=sr)
        
        destination_fc_name = f"osrm_destination_{now}"
        destination_fc = arcpy.CreateFeatureclass_management(
            default_db, destination_fc_name, waypoint_geometry, spatial_reference=sr)
        
        for f in [origin_fc, destination_fc]:
            arcpy.AddField_management(f, "name", "TEXT", field_length=128)
            
        with arcpy.da.InsertCursor(origin_fc, ["SHAPE@XY", "name"]) as ocur:
            ocur.insertRow([start["point"], start["coordstring"]])
            
        with arcpy.da.InsertCursor(destination_fc, ["SHAPE@XY", "name"]) as dcur:
            dcur.insertRow([end["point"], end["coordstring"]])
            
        waypoint_str_coords = []
        waypoint_layers = []
        waypoint_layer_count = 1
        
        if len(waypoint_dict) > 0:
            arcpy.SetProgressor("default", "Building Waypoint feature classes...")
            for k, v in waypoint_dict.items():
                # key: waypoint feature class name | value: [layer name, coordinate string, point geom]
                waypoint_str_coords.append(v[1])
                wp_fc = arcpy.CreateFeatureclass_management(
                    default_db, k, waypoint_geometry, spatial_reference=sr)
                arcpy.AddField_management(wp_fc, "name", "TEXT", field_length=128)
                with arcpy.da.InsertCursor(wp_fc, ["SHAPE@XY", "name"]) as wcur:
                    wcur.insertRow([v[2], v[1]])
                waypoint_layers.append([waypoint_layer_count, wp_fc])
                waypoint_layer_count += 1
            arcpy.AddMessage(waypoint_layers)
            
        # Query OSRM
        with open(OSRM_CONFIG_FILE, "r") as osrm_cfg:
            o = json.load(osrm_cfg)
            urldata = o["URL"]
            baseurl = urldata["BASE"]
            p2p_url = urldata["P2P"]
            p2p_wp_url = urldata["WITH_WAYPOINTS"]
            p2p_alts_url = urldata["P2P_ALTS"]
            p2p_alts_wp_url = urldata["WITH_WAYPOINTS_ALTS"]
            
            if alts:  # Get alternate routes
                if len(waypoint_str_coords) > 0:
                    waypoint_str = ";".join(waypoint_str_coords)
                    osrm_url = baseurl + (str(p2p_alts_wp_url)
                                          .replace("_ORIGIN_", origin)
                                          .replace("_DESTINATION_", destination)
                                          .replace("_WAYPOINTSTR_", waypoint_str))
                else:
                    osrm_url = baseurl + (str(p2p_alts_url)
                                          .replace("_ORIGIN_", origin)
                                          .replace("_DESTINATION_", destination))
            else:  # Get only primary route
                if len(waypoint_str_coords) > 0:
                    waypoint_str = ";".join(waypoint_str_coords)
                    osrm_url = baseurl + (str(p2p_wp_url)
                                          .replace("_ORIGIN_", origin)
                                          .replace("_DESTINATION_", destination)
                                          .replace("_WAYPOINTSTR_", waypoint_str))
                else:
                    osrm_url = baseurl + (str(p2p_url)
                                          .replace("_ORIGIN_", origin)
                                          .replace("_DESTINATION_", destination))
                    
            arcpy.SetProgressor("default", "Querying OSRM...")
            arcpy.AddMessage(f"OSRM URL: {osrm_url}")
            
            r = requests.get(osrm_url)
            # Uncomment for PKI usage
            #r = ArcPKI().get(osrm_url)
            if r.status_code == 200:
                arcpy.AddMessage("Got OSRM results.  Parsing...")
                osrm_r = r.json()
                
                route_fc_list = []
                route_count = 0
                routes = osrm_r["routes"]
                
                arcpy.SetProgressor("default", "Building route feature classes...")
                for route in routes:
                    out_name = f"osrm_rt_{route_count}_{now}"
                    geometry_type = "POLYLINE"
                    out_fc = arcpy.CreateFeatureclass_management(default_db, out_name, geometry_type,
                                                                 spatial_reference=sr)
                    fields = [
                        ["distance", "FLOAT"],
                        ["duration", "FLOAT"]
                    ]
                    arcpy.AddFields_management(out_fc, fields)
                    route_count += 1
                    
                    with arcpy.da.InsertCursor(out_fc, ["SHAPE@", "distance", "duration"]) as rcur:
                        legs = route["legs"]
                        for leg in legs:
                            steps = leg["steps"]
                            for step in steps:
                                geom = arcpy.AsShape(step["geometry"], False)
                                dist = step["distance"]
                                dur = step["duration"]
                                row = [geom, dist, dur]
                                rcur.insertRow(row)
                    route_fc_list.append(out_fc)
                arcpy.SetProgressor("default", "Adding results to map...")
                """
                Group layer management is not working yet
                grplyrfile = os.path.join(Path(os.path.dirname(__file__)).parent, "res", "New Group Layer.lyrx")
                grplyr = arcpy.mp.LayerFile(grplyrfile)
                
                osrm_group = active_map.addLayer(grplayer)[0]
                osrm_group.name = f"OSRM {now}"
                """
                for idx, rfc in enumerate(route_fc_list):
                    osrm_lyr = active_map.addDataFromPath(rfc)
                    if idx == 0:  # First route is primary/optimized route
                        osrm_lyr.name = "OSRM Route (Primary)"
                        rsym = osrm_lyr.symbology
                        rsym.renderer.symbol.size = 4
                        rsym.renderer.symbol.color = {"RGB": [165, 75, 255, 60]}
                        osrm_lyr.symbology = rsym
                    else:
                        osrm_lyr.name = "OSRM Route (Alternate)"
                        rsym = osrm_lyr.symbology
                        rsym.renderer.symbol.size = 3
                        rsym.renderer.symbol.color = {"RGB": [40, 40, 90, 30]}
                        osrm_lyr.symbology = rsym
                        
                # Add Destination
                destination_lyr = active_map.addDataFromPath(destination_fc)
                destination_lyr.name = f"{destination_label} (Destination)"
                dsym = destination_lyr.symbology
                dsym.renderer.symbol.size = 9
                dsym.renderer.symbol.color = {"RGB": [160, 0, 0, 100]}
                destination_lyr.symbology = dsym
                
                # Add Waypoints (if any)
                if len(waypoint_layers) > 0:
                    waypoint_layers = reversed(waypoint_layers)
                    for wl in waypoint_layers:
                        waypoint_lyr = active_map.addDataFromPath(wl[1])
                        if wl[0] < 10:
                            waypoint_lyr.name = f"Waypoint 0{wl[0]}"
                        else:
                            waypoint_lyr.name = f"Waypoint {wl[0]}"
                        wsym = waypoint_lyr.symbology
                        wsym.renderer.symbol.size = 9
                        wsym.renderer.symbol.color = {"RGB": [242, 239, 15, 100]}
                        waypoint_lyr.symbology = wsym
                        
                # Add Origin
                origin_lyr = active_map.addDataFromPath(origin_fc)
                origin_lyr.name = f"{origin_label} (Origin)"
                osym = origin_lyr.symbology
                osym.renderer.symbol.size = 9
                osym.renderer.symbol.color = {"RGB": [0, 160, 0, 100]}
                origin_lyr.symbology = osym
                
                # Done
                arcpy.AddMessage("Routing query complete.")
            else:
                arcpy.AddWarning("Could not get OSRM results.")
                raise ExceptionNetworkFailure
                
                
                
            
