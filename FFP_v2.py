# # Wrapper for the Klujn et al. 2015 flux footprint model
# import re
# import os
# # import utm_zone
# import numpy as np
# import pandas as pd
# import configparser
# import geopandas as gpd
# from functools import partial
# from multiprocessing import Pool
# from Klujn_2015_Model import FFP
# from collections import defaultdict


# from HelperFunctions import progressbar

# import random

# import matplotlib.pyplot as plt
import time
t1 = time.time()
import os
import numpy as np
import pandas as pd
import rasterio
from rasterio import features
from rasterio.transform import from_origin
from typing import Iterable
from dataclasses import dataclass, field, make_dataclass
from helperFunctions.baseClass import baseClass
from helperFunctions.parseCoordinates import parseCoordinates

print('import time', time.time()-t1)

# Database formatted site configuration file
siteConfigurationTemplate=r'C:\Users\User\GSC_Work\EC_processing\projectPath\siteMetadata\siteID\siteID_siteConfig.yml'
siteConfiguration = baseClass.fromTemplate(siteConfigurationTemplate)

print(siteConfiguration)
# print(siteConfiguration.fromTemplate(r'c:\Users\User\GSC_Work\EC_processing\testing\outputs\deltaEC\siteMetadata\SCL\SCL_siteConfig.yml'))
breakpoint()

@dataclass(kw_only=True)
class inputVariableNames:
    bearing: str = 'bearing' #Measurement direction offset from north
    zm: str = 'zm' # Measurement height above ground (give dynamically if variable) or set fixed value from ini file.\nWill automatically account for displacement height (zm-d).
    canopy_height: str = 'canopy_height' # Canopy height (m) can be a dynamic (from half-hourly input data) or static (from site configuration file).\nIf not provided in input data, a static value will be set using site_config file.
    z0: str = 'z0' # roughness length - provide explicitly if known, leave blank to auto calculate as a fraction of canopy height (see [Assumptions]). Leave blank AND set [Assumptions] roughness_length :  None to run without 
    h: str = 'hpbl' #Height of planetary boundary layer (m) - if not avaialble, see https://github.com/ubc-micromet/Biomet.net/blob/main/Python/ExtractNARR.py
    ol: str = 'L' #ol: Obukhov length (m)
    sigmav: str = 'V_SIGMA' #sigmav: Standard deviation of horizontal wind (m/s)
    ustar: str = 'USTAR' #ustar: Friction velocity (m/s)
    umean: str = 'wind_speed' #umean: Mean wind speed (m/s)\nNote the program expects u-mean, but will only actually be used if FFP is run without z0
    wind_dir: str = 'wind_dir' #wind_dir: Wind direction in degrees from north (deg)

@dataclass(kw_only=True)
class ffpParameters(baseClass):
    # Initialize static ffp domain parameters and FFP assumptions

    domain: int = 1000 # Upwind distance (m) over which to calculate.\n Resulting footprint will be calculated over circular area with a radius :  domain, centered on the lat,long coordinates of the EC Station.\n Outputs will be automatically georeferenced using lat,long coordinates of the EC Station.\nFFP - must be >:  600
    dx: int = 2 #Cell size of the raster grid:\nlarger cells :  faster runs & less precise outputs > smaller cell :  slower runs & more precise outputs
    rs: list = field(default_factory=lambda:[.5,.75,.9]) #Flux contribution contours (% level)
    exclude_wake: float = 30 # Dont calculate fluxes for observations with a wind_dir between (bearing -180) +/- exclude_wake 
    roughness_length: float = 0.15 # fraction of canopy height - these are the defaults used by EddyPro
    displacement_height: float = 0.67 #fraction of canopy height - these are the defaults used by EddyPro

    def __post_init__(self):

        # Number of cells 2 x domain / dx
        self.nx = int(self.domain*2 / self.dx)

        # gridded local coordinate system
        x = np.linspace(-self.domain, self.domain, self.nx, dtype=np.float32)
        self.x_2d, self.y_2d = np.meshgrid(x, x)

        # Polar coordinates
        # Set theta such that North is pointing upwards and angles increase clockwise
        self.rho = np.sqrt(self.x_2d**2 + self.y_2d**2)
        self.theta = np.arctan2(self.x_2d, self.y_2d)

        # Apply a symmetric mask to restrict summations to a radius of upwind_fetch around [0 0 zm]
        symetric_Mask = self.rho.copy()
        symetric_Mask[self.rho>self.domain] = np.nan
        self.symetric_Mask = symetric_Mask*0 + 1

        # initialize rasters for footprint climatology
        self.fclim_2d_empty = np.zeros(self.x_2d.shape,dtype=np.float32)
    

@dataclass(kw_only=True)
class ffpOverlay(ffpParameters):
    # Initialize site-specific parameters from a configuration file (or dict) and generate a site-specific basemap
    siteConfig: Iterable
    baseMap: str = None #path to vector or raster layer for overlaying with footprint climatology

    def __post_init__(self):
        super().__post_init__()
        if type(self.siteConfig) is str:
            self.siteConfig=self.loadDict(fileName=self.siteConfig)
        self.siteCoordinates = parseCoordinates(
            UID=self.siteConfig['siteID'],
            latitude=self.siteConfig['latitude'],
            longitude=self.siteConfig['longitude']
            )
        
    def rasterizeBasemap(self):
        # self.Transform = {}
        # self.baseVector = {}
        # self.baseRaster = {}
        # self.baseRasterKey = {}
        # self.Fc_Names = {}
        if self.baseMap is not None:
            print('Rasterizing basemap')
            print(self.siteCoordinates)
        # for self.sc in self.Site_code:
            # basemap=self.ini[self.sc]['basemap']
            # basemap_class=self.ini[self.sc]['basemap_class']
        #     x,y = self.Site_UTM.loc[self.Site_UTM.index==self.sc].geometry.x.values[0],self.Site_UTM.loc[self.Site_UTM.index==self.sc].geometry.y.values[0]
        #     west = x-(self.nx*self.dx)/2
        #     north = y+(self.nx*self.dx)/2
        #     self.Transform[self.sc] = from_origin(west,north,self.dx,self.dx)
            
        #     if os.path.isfile(basemap):
        #         # Read basemap layer and reproject if not already in the proper WGS 1984 Zone
        #         self.baseVector[self.sc] = gpd.read_file(basemap).to_crs(self.EPSG)
        #         self.baseVector[self.sc] = gpd.clip(self.baseVector[self.sc],self.Site_UTM.buffer(self.domain))
        #         if basemap_class != 'None' and basemap_class != '':
        #             self.baseVector[self.sc] = self.baseVector[self.sc].dissolve(by=basemap_class).reset_index()
        #         else:
        #             basemap_class = 'Unit'
        #             self.baseVector[self.sc][basemap_class]=self.baseVector[self.sc].index
        #             self.baseVector[self.sc] = self.baseVector[self.sc].dissolve().reset_index(drop=True)
        #         self.baseVector[self.sc].index+=1
        #         self.baseRasterKey[self.sc] = self.baseVector[self.sc][basemap_class].to_dict()
        #         self.Fc_Names[self.sc] = [self.baseRasterKey[self.sc][i]+'_Fc' for i in self.baseVector[self.sc].index.values]

        #         shapes = ((geom,value) for geom,value in zip(self.baseVector[self.sc]['geometry'],self.baseVector[self.sc].index))

        #         with rasterio.open(f"{self.ini['Output']['dpath']}/Footprint_Basemap_{self.sc}_{self.dx}m.tif",'w+',driver='GTiff',width = self.nx, height = self.nx,#+1,
        #                         count = 1,dtype=np.float32,transform = self.Transform[self.sc],crs = ({'init': f'EPSG:{self.EPSG}'})) as out:
        #             out_arr = out.read(1)
        #             self.baseRaster[self.sc] = features.rasterize(shapes=shapes,fill = 100,out = out_arr,transform = self.Transform[self.sc],default_value=-1)
        #             self.baseRaster[self.sc] = self.baseRaster[self.sc] * self.symetric_Mask
        #             out.write(self.baseRaster[self.sc],1)
        else: 
            print('Basemap not provided, creating default')
            self.baseRaster = self.symetric_Mask
            self.Fc_Names = []
            self.baseRasterKey = {f'Contribution within {self.domain} m':''}

@dataclass(kw_only=True)
class ffpClimatology(ffpOverlay,inputVariableNames):
    inputData: pd.DataFrame
    subsetCode: str = None #column in input_data denoting subset by which to partition footprint (e.g., Season)

    def __post_init__(self):
        super().__post_init__()
        
        # self.ffpGrid()
        
