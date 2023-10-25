import arcpy
from datetime import datetime
import os
from pathlib import Path
import sys

# Disable writing cache files
sys.dont_write_bytecode = True


ARMS_TABLE = {
    "RUS": [
    {
        "distance": 50,
        "label": "MP_443/MP-446/GSh-18/Makarov/Saiga-12",
        "rgba": {"RGB": [178, 178, 178, 100]}
    },
    {
        "distance": 200,
        "label": "RPG-18/RPG-26/RPG-27/RPG/30/SR-3",
        "rgba": {"RGB": [255, 190, 232, 100]}
    },
    {
        "distance": 300,
        "label": "AK-47/AKM/RPG-7",
        "rgba": {"RGB": [223, 115, 255, 100]}
    },
    {
        "distance": 400,
        "label": "AK-47/AKM/RPG-7",
        "rgba": {"RGB": [223, 115, 255, 100]}
    },
    {
        "distance": 500,
        "label": "RPK-74/RPG-29",
        "rgba": {"RGB": [190, 210, 255, 100]}
    },
    {
        "distance": 800,
        "label": "RPD/RPK/SPG-9/SVD-63/SV-98",
        "rgba": {"RGB": [0, 92, 230, 100]}
    },
    {
        "distance": 1000,
        "label": "PKM/SV-98",
        "rgba": {"RGB": [0, 38, 115, 100]}
    },
    {
        "distance": 1200,
        "label": "AGS-17",
        "rgba": {"RGB": [255, 190, 190, 100]}
    },
    {
        "distance": 1500,
        "label": "DShK/PKP/KSVK",
        "rgba": {"RGB": [255, 0, 0, 100]}
    },
    {
        "distance": 1700,
        "label": "AGS-30",
        "rgba": {"RGB": [168, 0, 0, 100]}
    },
    {
        "distance": 2000,
        "label": "NSV/AT-13/Kord-12.7mm/OSV-96",
        "rgba": {"RGB": [137, 68, 68, 100]}
    },
    {
        "distance": 2500,
        "label": "AT-4/AGS-40",
        "rgba": {"RGB": [190, 255, 232, 100]}
    },
    {
        "distance": 3040,
        "label": "M-37 82mm Mortar",
        "rgba": {"RGB": [68, 137, 122, 100]}
    },
    {
        "distance": 4000,
        "label": "AT-5",
        "rgba": {"RGB": [92, 137, 68, 100]}
    },
    {
        "distance": 4270,
        "label": "2B14 82mm Mortar",
        "rgba": {"RGB": [114, 137, 68, 100]}
    },
    {
        "distance": 5500,
        "label": "AT-14",
        "rgba": {"RGB": [137, 137, 68, 100]}
    },
    {
        "distance": 5700,
        "label": "M-38/4 120mm Mortar",
        "rgba": {"RGB": [223, 115, 255, 100]}
    },
    {
        "distance": 6000,
        "label": "2B24 107mm Mortar",
        "rgba": {"RGB": [255, 170, 0, 100]}
    },
    {
        "distance": 6300,
        "label": "M-38 107mm Mortar",
        "rgba": {"RGB": [168, 56, 0, 100]}
    },
    {
        "distance": 7100,
        "label": "2Bll 120mm Mortar",
        "rgba": {"RGB": [115, 0, 0, 100]}
    }
    ],
    "USA": [
    {
        "distance": 50,
        "label": "M9/M17/M18/M1911/M590/M4 Shotgun",
        "rgba": {"RGB": [178, 178, 178, 100]}
    }, 
    {
        "distance": 200,
        "label": "M72 LAW",
        "rgba": {"RGB": [255, 190, 232, 100]}
    }, 
    {
        "distance": 300,
        "label": "AT-4 Recoiless Rifle",
        "rgba": {"RGB": [223, 115, 255, 100]}
    },
    {
        "distance": 400,
        "label": "M32A1",
        "rgba": {"RGB": [0, 92, 230, 100]}
    },
    {
        "distance": 500,
        "label": "MK 153 SMAW/M4A1",
        "rgba": {"RGB": [190, 210, 255, 100]}
    },
    {
        "distance": 600,
        "label": "M14",
        "rgba": {"RGB": [0, 92, 230, 100]}
    },
    {
        "distance": 800,
        "label": "M16A2/Mk 17/M249 SAW/Mk 48/Mk 48/M39/M40",
        "rgba": {"RGB": [0, 38, 115, 100]}
    },
    {
        "distance": 1000,
        "label": "M141 SMAW-D/M3 MAAWS",
        "rgba": {"RGB": [255, 190, 190, 100]}
    },
    {
        "distance": 1200,
        "label": "M240/M60",
        "rgba": {"RGB": [230, 0, 0, 100]}
    },
    {
        "distance": 1500,
        "label": "Mk 19/M24 SWS",
        "rgba": {"RGB": [137, 68, 68, 100]}
    },
    {
        "distance": 1800,
        "label": "M2 Browning/M82 Barret/Mk 15",
        "rgba": {"RGB": [190, 255, 232, 100]}
    },
    {
        "distance": 3500,
        "label": "M224 60mm Mortar",
        "rgba": {"RGB": [233, 255, 190, 100]}
    },
    {
        "distance": 3750,
        "label": "BGM-71 TOW",
        "rgba": {"RGB": [137, 137, 68, 100]}
    },
    {
        "distance": 4000,
        "label": "FMG-148 Javelin",
        "rgba": {"RGB": [255, 170, 0, 100]}
    },
    {
        "distance": 5950,
        "label": "M252 81mm Mortar",
        "rgba": {"RGB": [168, 56, 0, 100]}
    },
    {
        "distance": 7250,
        "label": "M120 120mm Mortar",
        "rgba": {"RGB": [115, 0, 0, 100]}
    }
    ]
}


class SmallArmsRangeRings(object):
    
    def __init__(self):
        """
        Calculate multiple range rings based on common USA/NATO or Russian small arms.
        """
        self.category = "Analysis"
        self.name = "SmallArmsRangeRings"
        self.label = "Small Arms Range Rings"
        self.description = "Calculates multiple range rings based on common USA/NATO or Russian small arms."
        self.canRunInBackground = False     
    
    def getParameterInfo(self):
        """
        Define Parameters.
        """
        param0 = arcpy.Parameter(
            displayName="Origin Point of Polygon",
            name="in_fc",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input"
        )
        
        param1 = arcpy.Parameter(
            displayName="Arms Regime",
            name="arms_cty",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        
        arms_cty_list = ["Russia", "USA"]
        param1.filter.type = "ValueList"
        param1.filter.list = arms_cty_list
    
        return [param0, param1]

    def isLicensed(self):
        """
        Set whether tool is licensed to execute.
        """
        return True
    
    def updateParameters(self, parameters):
        """
        Modify the values and properties of parameters before internal
        validation is performed. This method is called whenever a parameter
        has been changed.
        """
        return True
    
    def updateMessages(self, parameters):
        """
        Modify messages created by internal validation for each tool 
        parameter. This method is called after internal validation.
        """
        return True

    def execute(self, parameters, messages):
        """
        Source code of the tool
        """
    
        #Environments
        arcpy.env.overwriteOutput = True
        p = arcpy.mp.ArcGISProject('CURRENT')
        active_map = p.activeMap
        default_gdb = p.defaultGeodatabase

        #Inputs
        in_fc = parameters[0].valueAsText
        arms_regime = parameters[1].valueAsText

        try:
            arcpy.SetProgressor("default", "Preparing initial settings...")
            
            if arms_regime == "Russia":
                arms = ARMS_TABLE["RUS"]
                cty = "RUS"
            else:
                arms = ARMS_TABLE["USA"]
                cty = "USA"

            arcpy.AddMessage(f"Running multiple ring buffer based on {cty} small arms table.")
        
            in_fc_desc = arcpy.Describe(in_fc)
            if in_fc_desc.shapeType == "Polygon":
                side_type = "OUTSIDE_ONLY"
            else:
                side_type ="FULL"
        
            distances = sorted([i['distance'] for i in arms])

            unit = 'meters'

            now = datetime.now().strftime("%Y%m%dT%H%M%S")
            out_fc = os.path.join(default_gdb, f"mrb_{cty}_{now}")

            arcpy.SetProgressor("default", "Running multi-ring buffer analysis...")
        
            mrb = arcpy.MultipleRingBuffer_analysis(
                in_fc,
                r"in_memory\mr_buffer",
                distances,
                unit,
                "",
                "NONE",
                side_type
            )
        
            arcpy.SetProgressor("default", "Updating weapon systems fields...")

            #Add fields and update with weapons/ranges
            arcpy.AddField_management(mrb, "WeaponSystem", "TEXT")
            fields = ["distance", "WeaponSystem"]
        
            with arcpy.da.UpdateCursor(mrb, fields) as cursor:
                for row in cursor:
                    for i in arms:
                        if row[0] == i["distance"]:
                            row[1] = i["label"]
                    cursor.updateRow(row)

            #Write to feature class
            arcpy.SetProgressor("default", "Writing output...")
            result = arcpy.CopyFeatures_management(mrb, out_fc)

            arcpy.SetProgressor("default", "Adding to map...")

            #Add to map and style 
            lyr = active_map.addDataFromPath(result)
            lyr.name = f"Small Arms Range Rings ({cty})"
            lsym = lyr.symbology
            lsym.updateRenderer('UniqueValueRenderer')

            lsym.renderer.fields = ['distance']
            for grp in lsym.renderer.groups:
                for itm in grp.items:
                    for i in arms:
                        if int(itm.values[0][0]) == i["distance"]:
                            itm.symbol.color = i["rgba"]
                            itm.label = f"""{str(i["distance"])}m: {i["label"]}"""
            lyr.symbology = lsym
            lyr.transparency = 50
    
        except Exception as e:
            raise e
        
