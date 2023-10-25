# IGEA GIS Tools

A collection of geospatial tools aimed at Army users for doing various Army things.  These tools 


* Terrain & Image to Collada Model _(3D Utilities)_

* Area Maximum Rise Over Run (AMROR) _(Analysis)_<br/>
* Build Cross Country Mobility Raster _(Analysis)_<br/>
* Create Canopy Height Model _(Analysis)_<br/>
* Helicopter Landing Zone Suitability _(Analysis)_<br/>
* Small Arms Range Rings _(Analysis)_<br/><br/>
* Add Coordinates to Attribute Table _(Conversions)_<br/>
* UTMizer _(Conversions)_<br/><br/>
* Query GETS Structured Object Data _(Research)_<br/>
* Query Ground Photography _(Research)_<br/>
* Query iSpy Coverage _(Research)_<br/><br/>
* Solve Route with OSRM _(Routing)_<br/>
* Create Distance Matrix with OSRM _(Routing)_<br/><br/>




## Installation and Dependencies

I've taken every effort to avoid dependencies external to the built-in Python instance that ships with ArcGIS Pro.  However, because PKI decryption is not supported natively in ArcGIS Pro's Python, the `requests_pkcs12` adapter must be installed before running the toolkit.  This is a fairly straightforward process but there are differences depending on whether you are on an Internet-connected workstation or not.


### On the Internet ###
**PKI handling is not yet implemented on internet connected systems.**  However, you will still need to install `requests_pkcs12` because it is imported upon toolbox loading.

In a `arcgispro-py3` Python prompt, do:

`pip install --user requests_pkcs12`

Then,

`git clone https://github.com/vovchykbratyk/gis_tools.git`

Add the folder containing `GISTools.pyt` to a project.

### On some other network ###

In a Powershell session, do...

`C:\path\to\ArcGISPro\bin\Python\envs\arcgispro-py3\Scripts\pip3.exe install --user --trusted-host <repository_domain> -i <repository_url> requests_pkcs12`

...replacing the obvious parts.  For example:

`C:\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\Scripts\pip3.exe install --user --trusted-host https://fake-example-repo.com -i https://fake-example-repo.com/pypi/simple requests_pkcs12`

This will install `requests_pkcs12` in your user space (no admin needed) but make it available to the built-in `arcgispro-py3` Python instance that ships with ArcGIS Pro.