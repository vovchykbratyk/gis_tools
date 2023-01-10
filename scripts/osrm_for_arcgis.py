import arcpy
from datetime import datetime, timedelta
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
    
    def build_url(self, origin, destination, waypoints: list, alts: bool):
        with open(OSRM_CONFIG_FILE, "r") as osrm_cfg:
            o = json.load(osrm_cfg)
            urldata = o["URL"]
            baseurl = urldata["BASE"]
            p2p_url = urldata["P2P"]
            p2p_wp_url = urldata["WITH_WAYPOINTS"]
            p2p_alts_url = urldata["P2P_ALTS"]
            wpw_alts_wp_url = urldata["WITH_WAYPOINTS_ALTS"]
            
            if alts:  # Get primary route and alternate routes
                if len(waypoints) > 0:
                    waypoint_str = ";".join(waypoints)
                    return baseurl + (str(p2p_alts_wp_url)
                                      .replace("_ORIGIN_", origin)
                                      .replace("_DESTINATION_", destination)
                                      .replace("_WAYPOINTSTR_", waypoint_str))
                else:
                    return baseurl + (str(p2p_alts_url)
                                      .replace("_ORIGIN_", origin)
                                      .replace("_DESTINATION_", destination))
            else:  # Get only primary route
                if len(waypoints) > 0:
                    waypoint_str = ";".join(waypoints)
                    return baseurl + (str(p2p_wp_url)
                                      .replace("_ORIGIN_", origin)
                                      .replace("_DESTINATION_", destination)
                                      .replace("_WAYPOINTSTR_", waypoint_str))
                else:
                    return baseurl + (str(p2p_url)
                                      .replace("_ORIGIN_", origin)
                                      .replace("_DESTINATION_", destination))
                
    def get_route_times(self, route_fcs: list):
        for route_num, fc in enumerate(route_fcs):
            dur, dist = 0, 0
            with arcpy.da.SearchCursor(fc, ["distance", "duration"]) as cursor:
                for row in cursor:
                    dist += row[0]
                    dur += row[1]
            hours, remainder = divmod(timedelta(seconds=dur).total_seconds(), 3600)
            minutes = divmod(remainder, 60)[0]
            total_dist_km = dist / 1000
            total_dist_mi = total_dist_km * 0.62137119223733
            if route_num == 0:
                route_name = "Primary route"
            else:
                route_name = f"Alternate route {route_num}"
            yield {
                "name": route_name,
                "time": f"{hours}:{minutes}",
                "km": round(total_dist_km, 2),
                "miles": round(total_dist_mi, 2)
            }
                
    def memory_to_active_map(self, memory_fc):
        active_map = arcpy.mp.ArcGISProject("CURRENT").activeMap
        lyr_results = arcpy.MakeFeatureLayer_management(
            memory_fc,
            arcpy.Describe(memory_fc).name)
        mem_lyr = lyr_results.getOutput(0)
        return active_map.addLayer(mem_lyr)[0]
    
    def now(self):
        return datetime.now().strftime("%Y%m%dT%H%M%S")
    
    def print_waypoints(self, waypoints: dict):
        arcpy.AddMessage("\t----------------------------BEGIN WAYPOINTS----------------------------")
        for i in waypoints.values():
            arcpy.AddMessage("\t\t{}".format(i["coordstring"]))
        arcpy.AddMessage("\t----------------------------END WAYPOINTS----------------------------")

    def set_waypoints(self, waypointstr: str, latlon_reversed: bool):
        waypoints = [w.replace("'", "").strip() for w in waypointstr.split(";")]
        return {f"waypoint_{str(idx).zfill(2)}": CoordConvert(val).to_osrm_dd(latlon_reversed) for idx, val in enumerate(waypoints)}
    
    def write_featureclass(self, fc, out_db):
        fc_name = arcpy.Describe(fc).name
        return arcpy.CopyFeatures_management(fc, os.path.join(out_db, fc_name))

    def execute(self, parameters, messages):
        
        # Environments
        now = self.now()
        
        # Constants
        waypoint_dict = None
        waypoint_str_coords = []
        waypoint_fc_list = []

        # User parameters
        latlon_reversed = parameters[3].value  # Will be True or False (Default)
        start = CoordConvert(parameters[0].valueAsText).to_osrm_dd(latlon_reversed)
        end = CoordConvert(parameters[2].valueAsText).to_osrm_dd(latlon_reversed)
        waypoints = parameters[1].valueAsText
        alts = parameters[4].value

        if waypoints:
            waypoint_dict = self.set_waypoints(waypoints, latlon_reversed)
                        
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
            "memory", origin_fc_name, waypoint_geometry, spatial_reference=sr)
        
        destination_fc_name = f"osrm_destination_{now}"
        destination_fc = arcpy.CreateFeatureclass_management(
            "memory", destination_fc_name, waypoint_geometry, spatial_reference=sr)

        for f in [origin_fc, destination_fc]:
            arcpy.AddField_management(f, "name", "TEXT", field_length=128)
            
        with arcpy.da.InsertCursor(origin_fc, ["SHAPE@XY", "name"]) as ocur:
            ocur.insertRow([start["point"], start["coordstring"]])
            
        with arcpy.da.InsertCursor(destination_fc, ["SHAPE@XY", "name"]) as dcur:
            dcur.insertRow([end["point"], end["coordstring"]])
            
        if waypoint_dict:
            if len(waypoint_dict) > 0:
                arcpy.SetProgressor("default", "Building Waypoint feature classes...")
                for k, v in waypoint_dict.items():
                    # key: waypoint feature class name | value: [layer name, coordinate string, point geom]
                    waypoint_str_coords.append(v["coordstring"])
                    wp_fc = arcpy.CreateFeatureclass_management(
                        "memory", k, waypoint_geometry, spatial_reference=sr)
                    arcpy.AddField_management(wp_fc, "name", "TEXT", field_length=128)
                    with arcpy.da.InsertCursor(wp_fc, ["SHAPE@XY", "name"]) as wcur:
                        wcur.insertRow([v["point"], v["coordstring"]])
                    waypoint_fc_list.append(wp_fc)
            
        # Query OSRM
        osrm_url = self.build_url(origin, destination, waypoint_str_coords, alts)
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
                
            arcpy.SetProgressor("default", "Building route feature classes...")
            for route in osrm_r["routes"]:
                out_name = f"osrm_rt_{route_count}_{now}"
                geometry_type = "POLYLINE"
                out_fc = arcpy.CreateFeatureclass_management("memory", out_name, geometry_type, spatial_reference=sr)
                fields = [
                    ["distance", "FLOAT"],
                    ["duration", "FLOAT"]]
                arcpy.AddFields_management(out_fc, fields)
                route_count += 1
                with arcpy.da.InsertCursor(out_fc, ["SHAPE@", "distance", "duration"]) as rcur:
                    for leg in route["legs"]:
                        for step in leg["steps"]:
                            geom = arcpy.AsShape(step["geometry"], False)
                            dist = step["distance"]
                            dur = step["duration"]
                            row = [geom, dist, dur]
                            rcur.insertRow(row)
                route_fc_list.append(out_fc)
                
            arcpy.SetProgressor("default", "Adding results to map...")
            routing_lyrs = []

            for idx, rfc in enumerate(route_fc_list):
                osrm_lyr = self.memory_to_active_map(rfc)
                routing_lyrs.append(osrm_lyr)
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
            destination_lyr = self.memory_to_active_map(destination_fc)
            destination_lyr.name = f"{destination_label} (Destination)"
            dsym = destination_lyr.symbology
            dsym.renderer.symbol.size = 9
            dsym.renderer.symbol.color = {"RGB": [160, 0, 0, 100]}
            destination_lyr.symbology = dsym
                
            # Add Waypoints (if any)
            if len(waypoint_fc_list) > 0:
                waypoint_lyrs = []
                for idx, wl in enumerate(waypoint_layers):
                    waypoint_lyr = self.memory_to_active_map(wl)
                    waypoint_lyrs.append(waypoint_lyr)
                    waypoint_lyr.name = f"Waypoint {str(idx).zfill(2)}"
                    wsym = waypoint_lyr.symbology
                    wsym.renderer.symbol.size = 9
                    wsym.renderer.symbol.color = {"RGB": [242, 239, 15, 100]}
                    waypoint_lyr.symbology = wsym
                        
            # Add Origin
            origin_lyr = self.memory_to_active_map(origin_fc)
            origin_lyr.name = f"{origin_label} (Origin)"
            osym = origin_lyr.symbology
            osym.renderer.symbol.size = 9
            osym.renderer.symbol.color = {"RGB": [0, 160, 0, 100]}
            origin_lyr.symbology = osym
            
            # Move to group layer
            m = arcpy.mp.ArcGISProject("CURRENT").activeMap
            empty_group = arcpy.mp.LayerFile(
                os.path.join(Path(os.path.dirname(__file__)).parent, "res", "New Group Layer.lyrx"))
            group = m.addLayer(empty_group, "TOP")[0]
            group.name = f"OSRM Route: {now}"
            if len(waypoint_fc_list) > 0:
                ordered_lyrs = routing_lyrs + [destination_lyr] + waypoint_lyrs + [origin_lyr]
            else:
                ordered_lyrs = routing_lyrs + [destination_lyr, origin_lyr]
            for lyr in ordered_lyrs:
                m.addLayerToGroup(group, lyr)
                m.removeLayer(lyr)
            
            # Done, Metrics
            nl = '\n\t'
            tb = '\t\t\t'
            arcpy.AddMessage("---------------------------------------------ROUTE SUMMARY---------------------------------------------")
            if len(waypoint_fc_list) > 0:
                arcpy.AddMessage(f"Routing complete: {nl}From {start['coordstring']} ({origin_name}) {nl}to {end['coordstring']} ({destination_name}), {nl}{tb}VIA:")
                self.print_waypoints(waypoint_dict)
            else:
                arcpy.AddMessage(f"Routing complete: {nl}From {start['coordstring']} ({origin_name}) {nl}to {end['coordstring']} ({destination_name})")
            route_stats = self.get_route_times(route_fc_list)
            for r in route_stats:
                arcpy.AddMessage(f"{r['name']} | Total time: {r['time']} | Total distance: {r['km']} KM ({r['miles']} Miles)")
            arcpy.AddMessage("---------------------------------------------ROUTE SUMMARY---------------------------------------------")
        else:
            arcpy.AddWarning("Could not get OSRM results.")
            raise ExceptionNetworkFailure
