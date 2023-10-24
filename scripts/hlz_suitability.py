"""HLZ Suitability

This module takes as input a DEM (surface model or bare earth), a landcover
raster (optional), vertical obstructions (optional) and landing zone candidates
as a Point layer (optional).

The user selects a helicopter platform and the data is analyzed and reclassified
to show possible landing zone candidates.

@Author: Bryan Huddleston
@Date: October 2023
@Credit: Bryan Huddleston, Eric Eagle
@Links:
"""

import arcpy
from arcpy.sa import Combine, Reclassify, SurfaceParameters, RemapRange, RemapValue
import json
import os
import sys

sys.dont_write_bytecode = True


# Globals
def get_config():
	cfg_file = os.path.join(os.path.dirname(__file__), 'cfg', 'hlz_config.json')
	with open(cfg_file) as data:
		cfg = json.load(data)
		return cfg

CFG = get_config()
PLATFORMS = CFG["platforms"]
REMAPS = CFG["remaps"]


class HLZSuitability(object):
	def __init__(self):
		"""Creates Slope from DSM or DEM for suitable helocopter landing zones within a study area."""
		self.category = 'Analysis'
		self.name = 'HLZSuitabilityAnalysis',
		self.label = 'HLZ Suitability Analysis'
		self.alias = 'HLZ Suitability Analysis',
		self.description = 'Calculates slop to reclass values to identify suitable areas for helocopter landing operations for CH-47 and UH-60 rotary wing aircraft.'
		self.canRunInBackground = False

	def getParameterInfo(self):

		param0 = arcpy.Parameter(
			displayName='Terrain Dataset',
			name='terrain_dem',
			datatype=['DERasterDataset', 'GPRasterLayer'],
			parameterType='Required',
			direction='Input')

		param1 = arcpy.Parameter(
			displayName='Platform',
			name='platform',
			datatype='GPString',
			parameterType='Required',
			direction='Input',
			multiValue=True)

		param2 = arcpy.Parameter(
			displayName='Landcover Data',
			name='lulc',
			datatype=['DERasterDataset', 'GPRasterLayer'],
			parameterType='Optional',
			direction='Input')

		param3 = arcpy.Parameter(
			displayName='Vertical Obstructions',
			name='vert_obs',
			datatype=['DEFeatureClass', 'GPFeatureLayer'],
			parameterType='Optional',
			direction='Input')
		
		param4 = arcpy.Parameter(
			displayName='HLZ Points',
			name='hlz',
			datatype=['DEFeatureClass', 'GPFeatureLayer'],
			parameterType='Optional',
			direction='Input')
		
		param5 = arcpy.Parameter(
			displayName='Processing area',
			name='processing_area',
			datatype='GPString',
			parameterType='Required',
			direction='Input')
		
		param1.filter.type = 'ValueList'
		# This way you can just add new platforms and their processing settings in
		# hlz_config.json and the script tool will automatically pick them up:
		param1.filter.list = (list(PLATFORMS.keys()))
		
		param5.filter.type = 'ValueList'
		param5.filter.list = ['View Extent', 'Terrain coverage extent']
		param5.value = 'View Extent'

		params = [param0, param1, param2, param3, param4, param5]

		return params

	def isLicensed(self):
		return True

	def updateParameters(self, parameters):
		return True
	
	def updateMessages(self, parameters):
		"""
		The first validation checks if the user's input data is projected. Then
		the deeper check inspects whether the input projections match, using the
		terrain source as the reference projection.
		"""
		epsg = None
		for idx, p in enumerate(parameters):
			if p.altered:
				if p.valueAsText and p.datatype in ['DERasterDataset', 'GPRasterLayer']:
					sr = arcpy.Describe(p.valueAsText).spatialReference
					if sr.type == 'Geographic':
						p.setErrorMessage('Input data must be projected.')
					else:
						if idx == 0:
							epsg = sr.factoryCode
						if epsg:
							if sr.factoryCode != epsg:
								p.setErrorMessage('Input data does not match terrain input projection.')

		return True
	
	def get_view_extent(self, sr):
		p = arcpy.mp.ArcGISProject("CURRENT")
		return p.activeView.camera.getExtent().projectAs(sr)

	def execute(self, parameters, messages):

		arcpy.CheckOutExtension('Spatial')
		arcpy.CheckOutExtension('ImageAnalyst')
		arcpy.env.overwriteOutput = True

		p = arcpy.mp.ArcGISProject('CURRENT')
		db = p.defaultGeodatabase
		m = p.activeMap
		arcpy.env.workspace = db

		dem = parameters[0].valueAsText
		plts = parameters[1].values
		lulc = parameters[2].valueAsText
		vert = parameters[3].valueAsText
		points = parameters[4].valueAsText

		proc_area = parameters[5].valueAsText
		if proc_area == 'View Extent':
			arcpy.env.extent = self.get_view_extent(
				sr=arcpy.Describe(dem).spatialReference
			)
		else:
			arcpy.env.extent = dem

		# Process Slope
		arcpy.SetProgressor('default', 'Calculating Slope...')
		slope_hlz = SurfaceParameters(
			in_raster=dem,
			parameter_type='SLOPE',
			output_slope_measurement='DEGREE')
		arcpy.AddMessage('Created slope...')

		# Reclass Slope
		rasters = {
			"slopes": [],
			"optional": {
				"land_cover": None,
				"vertical_obstructions": None
			}
		}

		for plt in plts:
			arcpy.AddMessage(f"PLATFORM: {plt}")
			arcpy.AddMessage("RECLASS VALUES FOR PLATFORM")
			arcpy.AddMessage(f'{PLATFORMS[plt]["reclass"]}')
			print(type(PLATFORMS[plt]["reclass"]))
			try:
				rm = RemapRange(PLATFORMS[plt]["reclass"])
				arcpy.AddMessage(rm)
				arcpy.AddMessage(type(rm))
			except Exception as e:
				arcpy.AddMessage("CAUGHT EXCEPTION!")
				arcpy.AddMessage(e)
				raise Exception
				
			reclassed_slope = Reclassify(
				slope_hlz,
				"VALUE",
				RemapRange(PLATFORMS[plt]["reclass"]),
				"NODATA"
			)
			reclassed_slope.save(PLATFORMS[plt]["shortname"])
			rasters['slopes'].append(reclassed_slope)

		if lulc:
			arcpy.SetProgressor('default', 'Adding landcover data...')
			arcpy.AddMessage('Adding landcover data.')
			land_fact = Reclassify(lulc, 'VALUE', RemapValue(REMAPS["lulc"], 'NODATA'))
			land_fact.save("HLZ_LULC")
			rasters['optional']['land_cover'] = land_fact
		
		if vert:
			arcpy.SetProgressor('default', 'Adding vertical obstructions...')
			arcpy.AddMessage('Adding vertical obstructions.')
			vert_ras = arcpy.FeatureToRaster_conversion(vert, 'OBJECTID', 'obs_ras', cell_size=5)
			vert_obs = Reclassify(vert_ras, 'VALUE', RemapRange(REMAPS["vobs"]))
			vert_obs.save("OBS_RAS")
			rasters['optional']['vertical_obstructions'] = vert_obs
		
		"""
		Now we have a dictionary that looks like
		{
		    "slopes": [
			    slope1,
				slope2
			],
			"optional": {
			    "land_cover": land_fact (or could be None),
				"vertical_obstructions": vert_obs (or could be None)
			}
		}

		We can run against one slope only but can write it to add in
		the extras if they're there in one loop
		"""

		options = rasters['optional']
		extras_list = [i for i in options.values() if i]
		field_list = [f'!{arcpy.Describe(v).name}!' for v in options.values() if v]
		outputs = []
		combos = []
		if any(extras_list):
			for slope in rasters['slopes']:
				combine_inputs = [slope] + [extras_list]
				hlz_combo = Combine(combine_inputs)
				hlz_combo.save(f'{slope}_enhanced')
				combos.append(hlz_combo)

			for c in combos:
				arcpy.SetProgressor('Final classification...')
				arcpy.AddField_management(c, 'HLZ_Stat', 'LONG')
				express = f'HighNum({field_list})'
				code_block = """def HighNum(lst): return max(lst)"""
				combo_reclass = arcpy.CalculateField_management(c, 'HLZ_Stat', express, 'PYTHON3', code_block)
				outputs.append(combo_reclass)
		else:
			outputs = rasters['slopes']

		# Symbolize
		arcpy.SetProgressor('default', 'Applying symbology...')
		for o in outputs:
			lyr = m.addDataFromPath(o)
			lyr.name = arcpy.Describe(o).name
			sym = lyr.symbology
			sym.updateColorizer('RasterClassifyColorizer')
			sym.colorizer.classificationField = [field.name for field in arcpy.ListFields(lyr) if field.name in ['HLZ_Stat', 'Value']][0]
			sym.colorizer.breakCount = 3
			sym.colorizer.colorRamp = p.listColorRamps('Slope')[0]
			sym.colorizer.noDataColor = {'RGB': [0, 0, 0, 0]}
			label = ['Pass', 'Fringe', 'Fail']
			count = 0
			for brk in sym.colorizer.classBreaks:
				brk.label = label[count]
				count += 1
			lyr.symbology = sym
			lyr.transparency = 40

		if points:
			buff_list = []
			arcpy.SetProgressor('default', 'Buffering...')
			arcpy.AddMessage('Creating clearance radius for HLZ points...')
			for plt in plts:
				buff = arcpy.PairwiseBuffer_analysis(
					points,
					PLATFORMS[plt]["fc_name"],
					PLATFORMS[plt]["clearance"],
					method='PLANAR')
				lz = m.addDataFromPath(buff)
				buff_list.append(lz)

			arcpy.SetProgressor('default', 'Symbolizing buffers...')

			for l in buff_list:
				sym = l.symbology
				
				sym.updateRenderer('UniqueValueRenderer')
				sym.renderer.fields = ['BUFF_DIST']

				# Apply symbology from gallery
				for grp in sym.renderer.groups:
					for itm in grp.items:
						val = int(itm.values[0][0])
						if val in [25, 40]:
							itm.symbol.applySymbolFromGallery('Offset Hatch Border, No Fill')
							if val == 25:
								itm.label = '25m Radius'
							if val == 40:
								itm.label = '40m Radius'
				l.symbology = sym
