# svgmaps

The code consists largely of three notebooks to create COVID-maps for US states colored by district from blank maps and csv-datafiles. 

First, there's a notebook states_mapcleaner.ipynb to cast the blank maps in the format we want. This notebook is especially messy, and may need some tweaking to get it to work (re-running chunks etc). 
Second, there's a notebook covid_mapmaker.ipynb to create the colored maps. 
Third, there's a notebook uploadfile.ipynb to upload the maps to Wikimedia Commons.

states_svg_albers contains the albers projection original maps that serve as input for mapcleaner. Blankmaps contains the result of mapcleaner and input for mapmaker. Data is the folder for data files. mapmaker will collect more up to date csv for the covid data, but you may want to manually update the rest. Finally, the files will be stored in output. 
