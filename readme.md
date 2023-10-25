# IGEA GIS Tools

A collection of geospatial tools aimed at Army users for doing various Army things.


* Terrain & Image to Collada Model _(3D Utilities)_<br/>
** Converts a terrain source and an associated image to a Collada and a texture.<br/><br/>
* Area Maximum Rise Over Run (AMROR) _(Analysis)_<br/>
** Calculate the maximum angle of inclination over a distance and azimuth for each cell in an area.<br/>
* Build Cross Country Mobility Raster _(Analysis)_<br/>
** Builds a cost raster from several weighted inputs.<br/>
* Create Canopy Height Model _(Analysis)_<br/>
** Derives a canopy height model (CHM) from a Digital Surface Model (DSM).<br/>
* Helicopter Landing Zone Suitability _(Analysis)_<br/>
** Determine suitable areas for landing helicopters with support for avoiding obstacles contained in both raster and vector data types.<br/>
* Small Arms Range Rings _(Analysis)_<br/>
** Rough visualization of small arms ranges based on various national arms inventories.<br/><br/>
* Add Coordinates to Attribute Table _(Conversions)_<br/>
** Does just what it says.  Adds lat/lon and MGRS as fields in a point feature class.<br/>
* UTMizer _(Conversions)_<br/>
** Automatically projects data (raster or vector) to an appropriate UTM zone.<br/>
<br/><br/>
* Query GETS Structured Object Data _(Research)_<br/>
** Placeholder.<br/>
* Query Ground Photography _(Research)_<br/>
** Placeholder. <br/>
* Query iSpy Coverage _(Research)_<br/>
** Placeholder.<br/><br/>
* Solve Route with OSRM _(Routing)_<br/>
** Allows user to solve routes quickly using an Open Source Routing Machine (OSRM) instance.<br/>
* Create Distance Matrix with OSRM _(Routing)_<br/>
** Solve Traveling Salesman Problem (TSP) routes using an OSRM instance.<br/><br/><br/>

## Installation and Dependencies

I've taken every effort to avoid dependencies external to the built-in Python instance that ships with ArcGIS Pro.  However, because PKI decryption is not supported natively in ArcGIS Pro's Python, the `requests_pkcs12` adapter must be installed before running the toolkit.  This is a fairly straightforward process but there are differences depending on whether you are on an Internet-connected workstation or not.


### On the Internet ###
**PKI handling is not yet implemented on internet connected systems.**  However, you will still need to install `requests_pkcs12` because it is imported upon toolbox loading.

In a `arcgispro-py3` Python prompt, do:

`pip install --user requests_pkcs12`

Then (if using git),

`git clone https://github.com/vovchykbratyk/gis_tools.git`

or, (if not using git), just do **Code** --> **Download Zip** from this repo's landing page.

Add the folder containing `GISTools.pyt` to a project.
<br/><br/>
### On some other network ###

In a Powershell session, do...

`C:\path\to\ArcGISPro\bin\Python\envs\arcgispro-py3\Scripts\pip3.exe install --user --trusted-host <repository_domain> -i <repository_url> requests_pkcs12`

...replacing the obvious parts.  For example:

`C:\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\Scripts\pip3.exe install --user --trusted-host https://fake-example-repo.com -i https://fake-example-repo.com/pypi/simple requests_pkcs12`

This will install `requests_pkcs12` in your user space (no admin needed) but make it available to the built-in `arcgispro-py3` Python instance that ships with ArcGIS Pro.