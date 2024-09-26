"""
Purpose:
    This script automatically projects a dataset (raster or vector) to an appropriate UTM zone.
    
Limitations:
    Does not work with KML.
"""

import arcpy
import os
import sys

# Disable cache file writing
sys.dont_write_bytecode = True

UTMGRID = {
        "type": "FeatureCollection",
        "name": "utm_zones_simplified",
        "features": [
            {"type": "Feature", "properties": {"FID": 54, "UTMZONES": "45N", "EPSG": 32645}, "geometry": {"type": "Polygon", "coordinates": [[[90.0000002, 8.0], [90.0000002, 84.0000001], [84.0000002, 84.0000001], [84.0000002, 0.0000001], [90.0000002, 0.0000001], [90.0000002, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 334, "UTMZONES": "54S", "EPSG": 32754}, "geometry": {"type": "Polygon", "coordinates": [[[144.0, -72.0], [144.0, 0.0000001], [138.0, 0.0000001], [138.0, -80.0], [144.0, -80.0], [144.0, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 346, "UTMZONES": "20S", "EPSG": 32720}, "geometry": {"type": "Polygon", "coordinates": [[[-59.9999999, -72.0], [-59.9999999, 0.0000001], [-65.9999999, 0.0000001], [-65.9999999, -80.0], [-59.9999999, -80.0], [-59.9999999, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 79, "UTMZONES": "54N", "EPSG": 32654}, "geometry": {"type": "Polygon", "coordinates": [[[144.0, 8.0], [144.0, 84.0000001], [138.0, 84.0000001], [138.0, 0.0000001], [144.0, 0.0000001], [144.0, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 4, "UTMZONES": "1N", "EPSG": 32601}, "geometry": {"type": "Polygon", "coordinates": [[[-174.0, 8.0], [-174.0, 84.0000001], [-179.9999885, 84.0000001], [-179.9999885, 0.0000001], [-174.0, 0.0000001], [-174.0, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 22, "UTMZONES": "11N", "EPSG": 32611}, "geometry": {"type": "Polygon", "coordinates": [[[-113.9999999, 8.0], [-113.9999999, 84.0000001], [-120.0, 84.0000001], [-120.0, 0.0000001], [-113.9999999, 0.0000001], [-113.9999999, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 418, "UTMZONES": "37S", "EPSG": 32737}, "geometry": {"type": "Polygon", "coordinates": [[[42.0000002, -72.0], [42.0000002, 0.0000001], [36.0000002, 0.0000001], [36.0000002, -80.0], [42.0000002, -80.0], [42.0000002, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 435, "UTMZONES": "41S", "EPSG": 32741}, "geometry": {"type": "Polygon", "coordinates": [[[66.0000002, -72.0], [66.0000002, 0.0000001], [60.0000002, 0.0000001], [60.0000002, -80.0], [66.0000002, -80.0], [66.0000002, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 348, "UTMZONES": "58S", "EPSG": 32758}, "geometry": {"type": "Polygon", "coordinates": [[[168.0, -72.0], [168.0, 0.0000001], [162.0, 0.0000001], [162.0, -80.0], [168.0, -80.0], [168.0, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 68, "UTMZONES": "50N", "EPSG": 32650}, "geometry": {"type": "Polygon", "coordinates": [[[120.0, 8.0], [120.0, 84.0000001], [114.0, 84.0000001], [114.0, 0.0000001], [120.0, 0.0000001], [120.0, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 40, "UTMZONES": "20N", "EPSG": 32620}, "geometry": {"type": "Polygon", "coordinates": [[[-59.9999999, 8.0], [-59.9999999, 84.0000001], [-65.9999999, 84.0000001], [-65.9999999, 0.0000001], [-59.9999999, 0.0000001], [-59.9999999, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 44, "UTMZONES": "41N", "EPSG": 32641}, "geometry": {"type": "Polygon", "coordinates": [[[66.0000002, 8.0], [66.0000002, 84.0000001], [60.0000002, 84.0000001], [60.0000002, 0.0000001], [66.0000002, 0.0000001], [66.0000002, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 8, "UTMZONES": "24N", "EPSG": 32624}, "geometry": {"type": "Polygon", "coordinates": [[[-35.9999999, 8.0], [-35.9999999, 84.0000001], [-41.9999999, 84.0000001], [-41.9999999, 0.0000001], [-35.9999999, 0.0000001], [-35.9999999, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 280, "UTMZONES": "5S", "EPSG": 32705}, "geometry": {"type": "Polygon", "coordinates": [[[-150.0, -72.0], [-150.0, 0.0000001], [-156.0, 0.0000001], [-156.0, -80.0], [-150.0, -80.0], [-150.0, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 382, "UTMZONES": "28S", "EPSG": 32728}, "geometry": {"type": "Polygon", "coordinates": [[[-11.9999999, -72.0], [-11.9999999, 0.0000001], [-17.9999999, 0.0000001], [-17.9999999, -80.0], [-11.9999999, -80.0], [-11.9999999, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 294, "UTMZONES": "45S", "EPSG": 32745}, "geometry": {"type": "Polygon", "coordinates": [[[90.0000002, -72.0], [90.0000002, 0.0000001], [84.0000002, 0.0000001], [84.0000002, -80.0], [90.0000002, -80.0], [90.0000002, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 11, "UTMZONES": "5N", "EPSG": 32605}, "geometry": {"type": "Polygon", "coordinates": [[[-150.0, 8.0], [-150.0, 84.0000001], [-156.0, 84.0000001], [-156.0, 0.0000001], [-150.0, 0.0000001], [-150.0, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 309, "UTMZONES": "11S", "EPSG": 32711}, "geometry": {"type": "Polygon", "coordinates": [[[-113.9999999, -72.0], [-113.9999999, 0.0000001], [-120.0, 0.0000001], [-120.0, -80.0], [-113.9999999, -80.0], [-113.9999999, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 311, "UTMZONES": "49S", "EPSG": 32749}, "geometry": {"type": "Polygon", "coordinates": [[[114.0, -72.0], [114.0, 0.0000001], [108.0, 0.0000001], [108.0, -80.0], [114.0, -80.0], [114.0, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 279, "UTMZONES": "1S", "EPSG": 32701}, "geometry": {"type": "Polygon", "coordinates": [[[-174.0, -72.0], [-174.0, 0.0000001], [-179.9999885, 0.0000001], [-179.9999885, -80.0], [-174.0, -80.0], [-174.0, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 16, "UTMZONES": "28N", "EPSG": 32628}, "geometry": {"type": "Polygon", "coordinates": [[[-11.9999999, 8.0], [-11.9999999, 84.0000001], [-17.9999999, 84.0000001], [-17.9999999, 0.0000001], [-11.9999999, 0.0000001], [-11.9999999, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 301, "UTMZONES": "9S", "EPSG": 32709}, "geometry": {"type": "Polygon", "coordinates": [[[-126.0, -72.0], [-126.0, 0.0000001], [-132.0, 0.0000001], [-132.0, -80.0], [-126.0, -80.0], [-126.0, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 66, "UTMZONES": "49N", "EPSG": 32649}, "geometry": {"type": "Polygon", "coordinates": [[[114.0, 8.0], [114.0, 84.0000001], [108.0, 84.0000001], [108.0, 0.0000001], [114.0, 0.0000001], [114.0, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 431, "UTMZONES": "40S", "EPSG": 32740}, "geometry": {"type": "Polygon", "coordinates": [[[60.0000002, -72.0], [60.0000002, 0.0000001], [54.0000002, 0.0000001], [54.0000002, -80.0], [60.0000002, -80.0], [60.0000002, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 363, "UTMZONES": "24S", "EPSG": 32724}, "geometry": {"type": "Polygon", "coordinates": [[[-35.9999999, -72.0], [-35.9999999, 0.0000001], [-41.9999999, 0.0000001], [-41.9999999, -80.0], [-35.9999999, -80.0], [-35.9999999, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 29, "UTMZONES": "15N", "EPSG": 32615}, "geometry": {"type": "Polygon", "coordinates": [[[-89.9999999, 8.0], [-89.9999999, 84.0000001], [-95.9999999, 84.0000001], [-95.9999999, 0.0000001], [-89.9999999, 0.0000001], [-89.9999999, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 342, "UTMZONES": "19S", "EPSG": 32719}, "geometry": {"type": "Polygon", "coordinates": [[[-65.9999999, -72.0], [-65.9999999, 0.0000001], [-71.9999999, 0.0000001], [-71.9999999, -80.0], [-65.9999999, -80.0], [-65.9999999, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 34, "UTMZONES": "36N", "EPSG": 32636}, "geometry": {"type": "Polygon", "coordinates": [[[36.0000002, 8.0], [36.0000002, 72.0000001], [30.0000002, 72.0000001], [30.0000002, 0.0000001], [36.0000002, 0.0000001], [36.0000002, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 90, "UTMZONES": "57N", "EPSG": 32657}, "geometry": {"type": "Polygon", "coordinates": [[[162.0, 8.0], [162.0, 84.0000001], [156.0, 84.0000001], [156.0, 0.0000001], [162.0, 0.0000001], [162.0, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 6, "UTMZONES": "23N", "EPSG": 32623}, "geometry": {"type": "Polygon", "coordinates": [[[-41.9999999, 8.0], [-41.9999999, 84.0000001], [-47.9999999, 84.0000001], [-47.9999999, 0.0000001], [-41.9999999, 0.0000001], [-41.9999999, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 398, "UTMZONES": "32S", "EPSG": 32732}, "geometry": {"type": "Polygon", "coordinates": [[[12.0000002, -72.0], [12.0000002, 0.0000001], [6.0000002, 0.0000001], [6.0000002, -80.0], [12.0000002, -80.0], [12.0000002, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 330, "UTMZONES": "53S", "EPSG": 32753}, "geometry": {"type": "Polygon", "coordinates": [[[138.0, -72.0], [138.0, 0.0000001], [132.0, 0.0000001], [132.0, -80.0], [138.0, -80.0], [138.0, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 26, "UTMZONES": "32N", "EPSG": 32632}, "geometry": {"type": "Polygon", "coordinates": [[[12.0000002, 8.0], [12.0000002, 72.0000001], [6.0000002, 72.0000001], [6.0000002, 64.0000002], [3.0000003, 64.0000002], [2.9999986, 55.9999995], [6.0000002, 56.0], [6.0000002, 0.0000001], [12.0000002, 0.0000001], [12.0000002, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 51, "UTMZONES": "44N", "EPSG": 32644}, "geometry": {"type": "Polygon", "coordinates": [[[84.0000002, 8.0], [84.0000002, 84.0000001], [78.0000002, 84.0000001], [78.0000002, 0.0000001], [84.0000002, 0.0000001], [84.0000002, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 323, "UTMZONES": "15S", "EPSG": 32715}, "geometry": {"type": "Polygon", "coordinates": [[[-89.9999999, -72.0], [-89.9999999, 0.0000001], [-95.9999999, 0.0000001], [-95.9999999, -80.0], [-89.9999999, -80.0], [-89.9999999, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 76, "UTMZONES": "53N", "EPSG": 32653}, "geometry": {"type": "Polygon", "coordinates": [[[138.0, 8.0], [138.0, 84.0000001], [132.0, 84.0000001], [132.0, 0.0000001], [138.0, 0.0000001], [138.0, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 343, "UTMZONES": "57S", "EPSG": 32757}, "geometry": {"type": "Polygon", "coordinates": [[[162.0, -72.0], [162.0, 0.0000001], [156.0, 0.0000001], [156.0, -80.0], [162.0, -80.0], [162.0, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 18, "UTMZONES": "9N", "EPSG": 32609}, "geometry": {"type": "Polygon", "coordinates": [[[-126.0, 8.0], [-126.0, 84.0000001], [-132.0, 84.0000001], [-132.0, 0.0000001], [-126.0, 0.0000001], [-126.0, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 413, "UTMZONES": "36S", "EPSG": 32736}, "geometry": {"type": "Polygon", "coordinates": [[[36.0000002, -72.0], [36.0000002, 0.0000001], [30.0000002, 0.0000001], [30.0000002, -80.0], [36.0000002, -80.0], [36.0000002, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 360, "UTMZONES": "23S", "EPSG": 32723}, "geometry": {"type": "Polygon", "coordinates": [[[-41.9999999, -72.0], [-41.9999999, 0.0000001], [-47.9999999, 0.0000001], [-47.9999999, -80.0], [-41.9999999, -80.0], [-41.9999999, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 42, "UTMZONES": "40N", "EPSG": 32640}, "geometry": {"type": "Polygon", "coordinates": [[[60.0000002, 8.0], [60.0000002, 84.0000001], [54.0000002, 84.0000001], [54.0000002, 0.0000001], [60.0000002, 0.0000001], [60.0000002, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 290, "UTMZONES": "44S", "EPSG": 32744}, "geometry": {"type": "Polygon", "coordinates": [[[84.0000002, -72.0], [84.0000002, 0.0000001], [78.0000002, 0.0000001], [78.0000002, -80.0], [84.0000002, -80.0], [84.0000002, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 375, "UTMZONES": "27S", "EPSG": 32727}, "geometry": {"type": "Polygon", "coordinates": [[[-17.9999999, -72.0], [-17.9999999, 0.0000001], [-23.9999999, 0.0000001], [-23.9999999, -80.0], [-17.9999999, -80.0], [-17.9999999, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 9, "UTMZONES": "4N", "EPSG": 32604}, "geometry": {"type": "Polygon", "coordinates": [[[-156.0, 8.0], [-156.0, 84.0000001], [-162.0, 84.0000001], [-162.0, 0.0000001], [-156.0, 0.0000001], [-156.0, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 38, "UTMZONES": "19N", "EPSG": 32619}, "geometry": {"type": "Polygon", "coordinates": [[[-65.9999999, 8.0], [-65.9999999, 84.0000001], [-71.9999999, 84.0000001], [-71.9999999, 0.0000001], [-65.9999999, 0.0000001], [-65.9999999, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 14, "UTMZONES": "27N", "EPSG": 32627}, "geometry": {"type": "Polygon", "coordinates": [[[-17.9999999, 8.0], [-17.9999999, 84.0000001], [-23.9999999, 84.0000001], [-23.9999999, 0.0000001], [-17.9999999, 0.0000001], [-17.9999999, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 299, "UTMZONES": "8S", "EPSG": 32708}, "geometry": {"type": "Polygon", "coordinates": [[[-132.0, -72.0], [-132.0, 0.0000001], [-138.0, 0.0000001], [-138.0, -80.0], [-132.0, -80.0], [-132.0, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 305, "UTMZONES": "10S", "EPSG": 32710}, "geometry": {"type": "Polygon", "coordinates": [[[-120.0, -72.0], [-120.0, 0.0000001], [-126.0, 0.0000001], [-126.0, -80.0], [-120.0, -80.0], [-120.0, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 20, "UTMZONES": "10N", "EPSG": 32610}, "geometry": {"type": "Polygon", "coordinates": [[[-120.0, 8.0], [-120.0, 84.0000001], [-126.0, 84.0000001], [-126.0, 0.0000001], [-120.0, 0.0000001], [-120.0, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 62, "UTMZONES": "48N", "EPSG": 32648}, "geometry": {"type": "Polygon", "coordinates": [[[108.0, 8.0], [108.0, 84.0000001], [102.0, 84.0000001], [102.0, 0.0000001], [108.0, 0.0000001], [108.0, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 27, "UTMZONES": "14N", "EPSG": 32614}, "geometry": {"type": "Polygon", "coordinates": [[[-95.9999999, 8.0], [-95.9999999, 84.0000001], [-101.9999999, 84.0000001], [-101.9999999, 0.0000001], [-95.9999999, 0.0000001], [-95.9999999, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 32, "UTMZONES": "35N", "EPSG": 32635}, "geometry": {"type": "Polygon", "coordinates": [[[30.0000002, 8.0], [30.0000002, 72.0000001], [32.9999986, 71.9999996], [32.9999996, 84.0000001], [20.9999986, 84.0000001], [20.9999996, 72.0000001], [24.0000002, 72.0000001], [24.0000002, 0.0000001], [30.0000002, 0.0000001], [30.0000002, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 276, "UTMZONES": "4S", "EPSG": 32704}, "geometry": {"type": "Polygon", "coordinates": [[[-156.0, -72.0], [-156.0, 0.0000001], [-162.0, 0.0000001], [-162.0, -80.0], [-156.0, -80.0], [-156.0, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 88, "UTMZONES": "56N", "EPSG": 32656}, "geometry": {"type": "Polygon", "coordinates": [[[156.0, 8.0], [156.0, 84.0000001], [150.0, 84.0000001], [150.0, 0.0000001], [156.0, 0.0000001], [156.0, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 338, "UTMZONES": "18S", "EPSG": 32718}, "geometry": {"type": "Polygon", "coordinates": [[[-71.9999999, -72.0], [-71.9999999, 0.0000001], [-77.9999999, 0.0000001], [-77.9999999, -80.0], [-71.9999999, -80.0], [-71.9999999, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 394, "UTMZONES": "31S", "EPSG": 32731}, "geometry": {"type": "Polygon", "coordinates": [[[6.0000002, -72.0], [6.0000002, 0.0000001], [0.0000001, 0.0000001], [0.0000001, -80.0], [6.0000002, -80.0], [6.0000002, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 425, "UTMZONES": "39S", "EPSG": 32739}, "geometry": {"type": "Polygon", "coordinates": [[[54.0000002, -72.0], [54.0000002, 0.0000001], [48.0000002, 0.0000001], [48.0000002, -80.0], [54.0000002, -80.0], [54.0000002, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 36, "UTMZONES": "18N", "EPSG": 32618}, "geometry": {"type": "Polygon", "coordinates": [[[-71.9999999, 8.0], [-71.9999999, 84.0000001], [-77.9999999, 84.0000001], [-77.9999999, 0.0000001], [-71.9999999, 0.0000001], [-71.9999999, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 2, "UTMZONES": "22N", "EPSG": 32622}, "geometry": {"type": "Polygon", "coordinates": [[[-47.9999999, 8.0], [-47.9999999, 84.0000001], [-53.9999999, 84.0000001], [-53.9999999, 0.0000001], [-47.9999999, 0.0000001], [-47.9999999, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 307, "UTMZONES": "48S", "EPSG": 32748}, "geometry": {"type": "Polygon", "coordinates": [[[108.0, -72.0], [108.0, 0.0000001], [102.0, 0.0000001], [102.0, -80.0], [108.0, -80.0], [108.0, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 326, "UTMZONES": "52S", "EPSG": 32752}, "geometry": {"type": "Polygon", "coordinates": [[[132.0, -72.0], [132.0, 0.0000001], [126.0, 0.0000001], [126.0, -80.0], [132.0, -80.0], [132.0, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 24, "UTMZONES": "31N", "EPSG": 32631}, "geometry": {"type": "Polygon", "coordinates": [[[6.0000002, 8.0], [6.0000002, 56.0000002], [3.0000003, 56.0000002], [3.0000003, 64.0000002], [6.0000002, 64.0000002], [6.0000002, 71.9999999], [9.0000006, 71.9999996], [8.9999986, 84.0000001], [0.0000001, 84.0000001], [0.0000001, 0.0000001], [6.0000002, 0.0000001], [6.0000002, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 410, "UTMZONES": "35S", "EPSG": 32735}, "geometry": {"type": "Polygon", "coordinates": [[[30.0000002, -72.0], [30.0000002, 0.0000001], [24.0000002, 0.0000001], [24.0000002, -80.0], [30.0000002, -80.0], [30.0000002, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 74, "UTMZONES": "52N", "EPSG": 32652}, "geometry": {"type": "Polygon", "coordinates": [[[132.0, 8.0], [132.0, 84.0000001], [126.0, 84.0000001], [126.0, 0.0000001], [132.0, 0.0000001], [132.0, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 39, "UTMZONES": "39N", "EPSG": 32639}, "geometry": {"type": "Polygon", "coordinates": [[[54.0000002, 8.0], [54.0000002, 84.0000001], [48.0000002, 84.0000001], [48.0000002, 0.0000001], [54.0000002, 0.0000001], [54.0000002, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 319, "UTMZONES": "14S", "EPSG": 32714}, "geometry": {"type": "Polygon", "coordinates": [[[-95.9999999, -72.0], [-95.9999999, 0.0000001], [-101.9999999, 0.0000001], [-101.9999999, -80.0], [-95.9999999, -80.0], [-95.9999999, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 59, "UTMZONES": "47N", "EPSG": 32647}, "geometry": {"type": "Polygon", "coordinates": [[[102.0, 8.0], [102.0, 84.0000001], [96.0000002, 84.0000001], [96.0000002, 0.0000001], [102.0, 0.0000001], [102.0, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 340, "UTMZONES": "56S", "EPSG": 32756}, "geometry": {"type": "Polygon", "coordinates": [[[156.0, -72.0], [156.0, 0.0000001], [150.0, 0.0000001], [150.0, -80.0], [156.0, -80.0], [156.0, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 17, "UTMZONES": "8N", "EPSG": 32608}, "geometry": {"type": "Polygon", "coordinates": [[[-132.0, 8.0], [-132.0, 84.0000001], [-138.0, 84.0000001], [-138.0, 0.0000001], [-132.0, 0.0000001], [-132.0, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 354, "UTMZONES": "22S", "EPSG": 32722}, "geometry": {"type": "Polygon", "coordinates": [[[-47.9999999, -72.0], [-47.9999999, 0.0000001], [-53.9999999, 0.0000001], [-53.9999999, -80.0], [-47.9999999, -80.0], [-47.9999999, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 353, "UTMZONES": "60S", "EPSG": 32760}, "geometry": {"type": "Polygon", "coordinates": [[[179.9999885, -80.0], [179.9999885, 0.0000001], [174.0, 0.0000001], [174.0, -80.0], [179.9999885, -80.0]]]}},
            {"type": "Feature", "properties": {"FID": 287, "UTMZONES": "43S", "EPSG": 32743}, "geometry": {"type": "Polygon", "coordinates": [[[78.0000002, -72.0], [78.0000002, 0.0000001], [72.0000002, 0.0000001], [72.0000002, -80.0], [78.0000002, -80.0], [78.0000002, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 7, "UTMZONES": "3N", "EPSG": 32603}, "geometry": {"type": "Polygon", "coordinates": [[[-162.0, 8.0], [-162.0, 84.0000001], [-168.0, 84.0000001], [-168.0, 0.0000001], [-162.0, 0.0000001], [-162.0, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 47, "UTMZONES": "43N", "EPSG": 32643}, "geometry": {"type": "Polygon", "coordinates": [[[78.0000002, 8.0], [78.0000002, 84.0000001], [72.0000002, 84.0000001], [72.0000002, 0.0000001], [78.0000002, 0.0000001], [78.0000002, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 12, "UTMZONES": "26N", "EPSG": 32626}, "geometry": {"type": "Polygon", "coordinates": [[[-23.9999999, 8.0], [-23.9999999, 84.0000001], [-29.9999999, 84.0000001], [-29.9999999, 0.0000001], [-23.9999999, 0.0000001], [-23.9999999, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 295, "UTMZONES": "7S", "EPSG": 32707}, "geometry": {"type": "Polygon", "coordinates": [[[-138.0, -72.0], [-138.0, 0.0000001], [-144.0, 0.0000001], [-144.0, -80.0], [-138.0, -80.0], [-138.0, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 302, "UTMZONES": "47S", "EPSG": 32747}, "geometry": {"type": "Polygon", "coordinates": [[[102.0, -72.0], [102.0, 0.0000001], [96.0000002, 0.0000001], [96.0000002, -80.0], [102.0, -80.0], [102.0, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 15, "UTMZONES": "7N", "EPSG": 32607}, "geometry": {"type": "Polygon", "coordinates": [[[-138.0, 8.0], [-138.0, 84.0000001], [-144.0, 84.0000001], [-144.0, 0.0000001], [-138.0, 0.0000001], [-138.0, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 30, "UTMZONES": "34N", "EPSG": 32634}, "geometry": {"type": "Polygon", "coordinates": [[[24.0000002, 8.0], [24.0000002, 72.0000001], [18.0000002, 72.0000001], [18.0000002, 0.0000001], [24.0000002, 0.0000001], [24.0000002, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 25, "UTMZONES": "13N", "EPSG": 32613}, "geometry": {"type": "Polygon", "coordinates": [[[-101.9999999, 8.0], [-101.9999999, 84.0000001], [-107.9999999, 84.0000001], [-107.9999999, 0.0000001], [-101.9999999, 0.0000001], [-101.9999999, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 331, "UTMZONES": "17S", "EPSG": 32717}, "geometry": {"type": "Polygon", "coordinates": [[[-77.9999999, -72.0], [-77.9999999, 0.0000001], [-83.9999999, 0.0000001], [-83.9999999, -80.0], [-77.9999999, -80.0], [-77.9999999, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 322, "UTMZONES": "51S", "EPSG": 32751}, "geometry": {"type": "Polygon", "coordinates": [[[126.0, -72.0], [126.0, 0.0000001], [120.0, 0.0000001], [120.0, -80.0], [126.0, -80.0], [126.0, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 273, "UTMZONES": "3S", "EPSG": 32703}, "geometry": {"type": "Polygon", "coordinates": [[[-162.0, -72.0], [-162.0, 0.0000001], [-168.0, 0.0000001], [-168.0, -80.0], [-162.0, -80.0], [-162.0, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 83, "UTMZONES": "55N", "EPSG": 32655}, "geometry": {"type": "Polygon", "coordinates": [[[150.0, 8.0], [150.0, 84.0000001], [144.0, 84.0000001], [144.0, 0.0000001], [150.0, 0.0000001], [150.0, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 373, "UTMZONES": "26S", "EPSG": 32726}, "geometry": {"type": "Polygon", "coordinates": [[[-23.9999999, -72.0], [-23.9999999, 0.0000001], [-29.9999999, 0.0000001], [-29.9999999, -80.0], [-23.9999999, -80.0], [-23.9999999, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 390, "UTMZONES": "30S", "EPSG": 32730}, "geometry": {"type": "Polygon", "coordinates": [[[0.0000001, -72.0], [0.0000001, 0.0000001], [-5.9999999, 0.0000001], [-5.9999999, -80.0], [0.0000001, -80.0], [0.0000001, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 422, "UTMZONES": "38S", "EPSG": 32738}, "geometry": {"type": "Polygon", "coordinates": [[[48.0000002, -72.0], [48.0000002, 0.0000001], [42.0000002, 0.0000001], [42.0000002, -80.0], [48.0000002, -80.0], [48.0000002, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 33, "UTMZONES": "17N", "EPSG": 32617}, "geometry": {"type": "Polygon", "coordinates": [[[-77.9999999, 8.0], [-77.9999999, 84.0000001], [-83.9999999, 84.0000001], [-83.9999999, 0.0000001], [-77.9999999, 0.0000001], [-77.9999999, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 21, "UTMZONES": "30N", "EPSG": 32630}, "geometry": {"type": "Polygon", "coordinates": [[[0.0000001, 8.0], [0.0000001, 84.0000001], [-5.9999999, 84.0000001], [-5.9999999, 0.0000001], [0.0000001, 0.0000001], [0.0000001, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 37, "UTMZONES": "38N", "EPSG": 32638}, "geometry": {"type": "Polygon", "coordinates": [[[48.0000002, 8.0], [48.0000002, 84.0000001], [42.0000002, 84.0000001], [42.0000002, 0.0000001], [48.0000002, 0.0000001], [48.0000002, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 316, "UTMZONES": "13S", "EPSG": 32713}, "geometry": {"type": "Polygon", "coordinates": [[[-101.9999999, -72.0], [-101.9999999, 0.0000001], [-107.9999999, 0.0000001], [-107.9999999, -80.0], [-101.9999999, -80.0], [-101.9999999, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 95, "UTMZONES": "59N", "EPSG": 32659}, "geometry": {"type": "Polygon", "coordinates": [[[174.0, 8.0], [174.0, 84.0000001], [168.0, 84.0000001], [168.0, 0.0000001], [174.0, 0.0000001], [174.0, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 98, "UTMZONES": "60N", "EPSG": 32660}, "geometry": {"type": "Polygon", "coordinates": [[[179.9999885, 0.0000001], [179.9999885, 84.0000001], [174.0, 84.0000001], [174.0, 0.0000001], [179.9999885, 0.0000001]]]}},
            {"type": "Feature", "properties": {"FID": 406, "UTMZONES": "34S", "EPSG": 32734}, "geometry": {"type": "Polygon", "coordinates": [[[24.0000002, -72.0], [24.0000002, 0.0000001], [18.0000002, 0.0000001], [18.0000002, -80.0], [24.0000002, -80.0], [24.0000002, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 337, "UTMZONES": "55S", "EPSG": 32755}, "geometry": {"type": "Polygon", "coordinates": [[[150.0, -72.0], [150.0, 0.0000001], [144.0, 0.0000001], [144.0, -80.0], [150.0, -80.0], [150.0, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 56, "UTMZONES": "46N", "EPSG": 32646}, "geometry": {"type": "Polygon", "coordinates": [[[96.0000002, 8.0], [96.0000002, 84.0000001], [90.0000002, 84.0000001], [90.0000002, 0.0000001], [96.0000002, 0.0000001], [96.0000002, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 352, "UTMZONES": "21S", "EPSG": 32721}, "geometry": {"type": "Polygon", "coordinates": [[[-53.9999999, -72.0], [-53.9999999, 0.0000001], [-59.9999999, 0.0000001], [-59.9999999, -80.0], [-53.9999999, -80.0], [-53.9999999, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 284, "UTMZONES": "42S", "EPSG": 32742}, "geometry": {"type": "Polygon", "coordinates": [[[72.0000002, -72.0], [72.0000002, 0.0000001], [66.0000002, 0.0000001], [66.0000002, -80.0], [72.0000002, -80.0], [72.0000002, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 350, "UTMZONES": "59S", "EPSG": 32759}, "geometry": {"type": "Polygon", "coordinates": [[[174.0, -72.0], [174.0, 0.0000001], [168.0, 0.0000001], [168.0, -80.0], [174.0, -80.0], [174.0, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 41, "UTMZONES": "21N", "EPSG": 32621}, "geometry": {"type": "Polygon", "coordinates": [[[-53.9999999, 8.0], [-53.9999999, 84.0000001], [-59.9999999, 84.0000001], [-59.9999999, 0.0000001], [-53.9999999, 0.0000001], [-53.9999999, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 5, "UTMZONES": "2N", "EPSG": 32602}, "geometry": {"type": "Polygon", "coordinates": [[[-168.0, 8.0], [-168.0, 84.0000001], [-174.0, 84.0000001], [-174.0, 0.0000001], [-168.0, 0.0000001], [-168.0, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 10, "UTMZONES": "25N", "EPSG": 32625}, "geometry": {"type": "Polygon", "coordinates": [[[-29.9999999, 8.0], [-29.9999999, 84.0000001], [-35.9999999, 84.0000001], [-35.9999999, 0.0000001], [-29.9999999, 0.0000001], [-29.9999999, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 291, "UTMZONES": "6S", "EPSG": 32706}, "geometry": {"type": "Polygon", "coordinates": [[[-144.0, -72.0], [-144.0, 0.0000001], [-150.0, 0.0000001], [-150.0, -80.0], [-144.0, -80.0], [-144.0, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 71, "UTMZONES": "51N", "EPSG": 32651}, "geometry": {"type": "Polygon", "coordinates": [[[126.0, 8.0], [126.0, 84.0000001], [120.0, 84.0000001], [120.0, 0.0000001], [126.0, 0.0000001], [126.0, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 46, "UTMZONES": "42N", "EPSG": 32642}, "geometry": {"type": "Polygon", "coordinates": [[[72.0000002, 8.0], [72.0000002, 84.0000001], [66.0000002, 84.0000001], [66.0000002, 0.0000001], [72.0000002, 0.0000001], [72.0000002, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 297, "UTMZONES": "46S", "EPSG": 32746}, "geometry": {"type": "Polygon", "coordinates": [[[96.0000002, -72.0], [96.0000002, 0.0000001], [90.0000002, 0.0000001], [90.0000002, -80.0], [96.0000002, -80.0], [96.0000002, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 386, "UTMZONES": "29S", "EPSG": 32729}, "geometry": {"type": "Polygon", "coordinates": [[[-5.9999999, -72.0], [-5.9999999, 0.0000001], [-11.9999999, 0.0000001], [-11.9999999, -80.0], [-5.9999999, -80.0], [-5.9999999, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 23, "UTMZONES": "12N", "EPSG": 32612}, "geometry": {"type": "Polygon", "coordinates": [[[-107.9999999, 8.0], [-107.9999999, 84.0000001], [-113.9999999, 84.0000001], [-113.9999999, 0.0000001], [-107.9999999, 0.0000001], [-107.9999999, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 13, "UTMZONES": "6N", "EPSG": 32606}, "geometry": {"type": "Polygon", "coordinates": [[[-144.0, 8.0], [-144.0, 84.0000001], [-150.0, 84.0000001], [-150.0, 0.0000001], [-144.0, 0.0000001], [-144.0, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 19, "UTMZONES": "29N", "EPSG": 32629}, "geometry": {"type": "Polygon", "coordinates": [[[-5.9999999, 8.0], [-5.9999999, 84.0000001], [-11.9999999, 84.0000001], [-11.9999999, 0.0000001], [-5.9999999, 0.0000001], [-5.9999999, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 28, "UTMZONES": "33N", "EPSG": 32633}, "geometry": {"type": "Polygon", "coordinates": [[[18.0000002, 8.0], [18.0000002, 72.0000001], [20.9999996, 71.9999996], [20.9999986, 84.0000001], [8.9999986, 84.0000001], [8.9999986, 71.9999996], [12.0000002, 71.9999996], [12.0000002, 0.0000001], [18.0000002, 0.0000001], [18.0000002, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 271, "UTMZONES": "2S", "EPSG": 32702}, "geometry": {"type": "Polygon", "coordinates": [[[-168.0, -72.0], [-168.0, 0.0000001], [-174.0, 0.0000001], [-174.0, -80.0], [-168.0, -80.0], [-168.0, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 327, "UTMZONES": "16S", "EPSG": 32716}, "geometry": {"type": "Polygon", "coordinates": [[[-83.9999999, -72.0], [-83.9999999, 0.0000001], [-89.9999999, 0.0000001], [-89.9999999, -80.0], [-83.9999999, -80.0], [-83.9999999, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 315, "UTMZONES": "50S", "EPSG": 32750}, "geometry": {"type": "Polygon", "coordinates": [[[120.0, -72.0], [120.0, 0.0000001], [114.0, 0.0000001], [114.0, -80.0], [120.0, -80.0], [120.0, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 31, "UTMZONES": "16N", "EPSG": 32616}, "geometry": {"type": "Polygon", "coordinates": [[[-83.9999999, 8.0], [-83.9999999, 84.0000001], [-89.9999999, 84.0000001], [-89.9999999, 0.0000001], [-83.9999999, 0.0000001], [-83.9999999, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 370, "UTMZONES": "25S", "EPSG": 32725}, "geometry": {"type": "Polygon", "coordinates": [[[-29.9999999, -72.0], [-29.9999999, 0.0000001], [-35.9999999, 0.0000001], [-35.9999999, -80.0], [-29.9999999, -80.0], [-29.9999999, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 92, "UTMZONES": "58N", "EPSG": 32658}, "geometry": {"type": "Polygon", "coordinates": [[[168.0, 8.0], [168.0, 84.0000001], [162.0, 84.0000001], [162.0, 0.0000001], [168.0, 0.0000001], [168.0, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 402, "UTMZONES": "33S", "EPSG": 32733}, "geometry": {"type": "Polygon", "coordinates": [[[18.0000002, -72.0], [18.0000002, 0.0000001], [12.0000002, 0.0000001], [12.0000002, -80.0], [18.0000002, -80.0], [18.0000002, -72.0]]]}},
            {"type": "Feature", "properties": {"FID": 35, "UTMZONES": "37N", "EPSG": 32637}, "geometry": {"type": "Polygon", "coordinates": [[[42.0000002, 8.0], [42.0000002, 84.0000001], [32.9999996, 84.0000001], [32.9999986, 71.9999996], [36.0000002, 72.0000001], [36.0000002, 0.0000001], [42.0000002, 0.0000001], [42.0000002, 8.0]]]}},
            {"type": "Feature", "properties": {"FID": 313, "UTMZONES": "12S", "EPSG": 32712}, "geometry": {"type": "Polygon", "coordinates": [[[-107.9999999, -72.0], [-107.9999999, 0.0000001], [-113.9999999, 0.0000001], [-113.9999999, -80.0], [-107.9999999, -80.0], [-107.9999999, -72.0]]]}}
        ]
    }


class UTMizer(object):
    
    def __init__(self):
        self.category = "Conversions"
        self.name = "UTMizer"
        self.label = "UTMizer"
        self.description = "Automatically reprojects a raster or vector dataset to an appropriate UTM zone"
        self.canRunInBackground = False
        
    def getParameterInfo(self):
        
        param0 = arcpy.Parameter(
            displayName="Input Dataset",
            name="input_dataset",
            datatype=["GPFeatureLayer", "DEFeatureClass", "GPRasterLayer", "DERasterDataset"],
            parameterType="Required",
            direction="Input"
        )
        
        return [param0]
    
    def isLicensed(self):
        return True
    
    def updateParameters(self, parameters):
        return True
    
    def updateMessages(self, parameters):
        return True
    
    def make_temp_utm_fc(self, gj_string):
        sr = arcpy.SpatialReference(4326)
        temp_fc = arcpy.CreateFeatureclass_management(
            "memory", "utmzones", "POLYGON", spatial_reference=sr)
        arcpy.AddField_management(temp_fc, "EPSG", "TEXT")
        
        with arcpy.da.InsertCursor(temp_fc, ["SHAPE@", "EPSG"]) as irows:
            for feature in gj_string["features"]:
                geom = arcpy.AsShape(feature["geometry"], False)
                irows.insertRow([geom, feature["properties"]["EPSG"]])
        return temp_fc
    
    def get_extent_centroid(self, layer):
        gcs_sr = arcpy.SpatialReference(4326)
        return arcpy.Describe(layer).extent.polygon.projectAs(gcs_sr).centroid
    
    def execute(self, parameters, messages):
        
        # Environments
        p = arcpy.mp.ArcGISProject("CURRENT")
        activeMap = p.activeMap
        arcpy.env.overwriteOutput = True
        
        # Do the work
        try:
            gcs = arcpy.SpatialReference(4326)
            in_lyr = parameters[0].valueAsText
            
            arcpy.SetProgressor("default", "Initializing UTM grid...")
            utm_fc = self.make_temp_utm_fc(UTMGRID)
            
            arcpy.SetProgressor("default", "Getting layer information...")
            in_lyr_desc = arcpy.Describe(in_lyr)
            
            arcpy.SetProgressor("default", "Getting layer centroid...")
            center = self.get_extent_centroid(in_lyr)
            
            center_fc = arcpy.CreateFeatureclass_management(
                "memory", "layercenter", "POINT", spatial_reference=gcs)
            
            center_row = [(center.X, center.Y)]
            arcpy.AddMessage(f"Layer centroid: {center.Y}, {center.X}")
            with arcpy.da.InsertCursor(center_fc, ["SHAPE@XY"]) as cursor:
                cursor.insertRow(center_row)
                
            arcpy.SetProgressor("default", "Running spatial join...")
            center_fc_layer = arcpy.MakeFeatureLayer_management(center_fc, "center_fc_lyr")
            utm_fc_layer = arcpy.MakeFeatureLayer_management(utm_fc, "utm_fc_lyr")
            sj = arcpy.analysis.SpatialJoin(center_fc_layer, utm_fc_layer, os.path.join("memory", "sj"))
            
            arcpy.SetProgressor("default", "Getting UTM EPSG code...")
            epsg = None
            
            with arcpy.da.SearchCursor(sj, "EPSG") as cursor:
                for row in cursor:
                    arcpy.AddMessage(f"UTM EPSG code: {row[0]}")
                    epsg = int(row[0])
                    
            arcpy.SetProgressor("default", f"Projecting layer to EPSG:{str(epsg)}...")
            if hasattr(in_lyr, "name"):
                if len(str(in_lyr.name)) > 16:
                    original_name = str(in_lyr.name[:16])
                else:
                    original_name = str(in_lyr.name)
                original_name = original_name.replace(" ", "").replace(".", "_")
                utm_out_name = ("UTM_" + original_name).replace(".", "_").replace(" ", "")
            else:
                if len(str(in_lyr_desc.file)) > 16:
                    original_name = str(in_lyr_desc.file[:16])
                else:
                    original_name = str(in_lyr_desc.file)
                original_name = original_name.replace(".", "_").replace("-", "_").replace(" ", "")
                utm_out_name = str("UTM_" + original_name).replace(".", "_").replace("-", ")").replace("__", "_")
                
            if in_lyr_desc.dataType in ["FeatureLayer", "FeatureClass"]:
                # Do vector reprojection
                utm_reproj = arcpy.Project_management(in_lyr, utm_out_name, arcpy.SpatialReference(epsg))
                arcpy.AddMessage(f"Projected {original_name} to EPSG:{epsg} (Output dataset: {utm_out_name}).")
            elif in_lyr_desc.dataType in ["RasterLayer", "RasterDataset"]:
                # Do raster reprojection
                utm_reproj = arcpy.ProjectRaster_management(in_lyr, utm_out_name, arcpy.SpatialReference(epsg))
                arcpy.AddMessage(f"Projected {original_name} to EPSG:{epsg} (Output dataset: {utm_out_name}).")
                
            out_layer = activeMap.addDataFromPath(utm_reproj)
            out_layer.name = f"{original_name}_UTM"
            
        except arcpy.ExecuteError:
            arcpy.AddMessage(arcpy.GetMessages())
            raise arcpy.ExecuteError
    
