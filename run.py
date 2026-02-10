from FFP_v2 import ffpClimatology
import pandas as pd

# # siteConfig = {
# #     'SCL':{  
# #         'site_name': 'Swiss Cheese Lake',
# #         'altitude': 0,
# #         'latitude': 69.226625,
# #         'longitude': -135.250416,
# #         'canopy_height': 0.45,
# #         'zm': 2.87,
# #         'bearing':33,
# #         # 'time_zone' = Etc/GMT+7
# #         # start_year = 2017
# #     }
# # }
inputData = pd.read_csv(r'FFP_Inputs\FFP_Inputs_FishIsland.csv')
siteConfig = r'C:\Users\User\GSC_Work\EC_processing\testing\outputs\deltaEC\siteMetadata\SCL\SCL_siteConfig.yml'
baseMap = r'FFP_Inputs\Landscape_Classification_BigLakePlain.geojson'
ffpClimatology(inputData=inputData,siteConfig=siteConfig,baseMap=baseMap)


# import ruamel.yaml as YAML
# yaml = YAML()
# f = r'C:\Users\User\GSC_Work\EC_processing\testing\outputs\test\siteMetadata\siteID\siteID_siteConfig.yml'
# with open(f) as y:
#     site_config = yaml.safe_load(y)

# from dataclasses import make_dataclass
# # dcInfo = []
# # for key,value in site_config.items():
# #     if type(value) is None:

# # siteConfig = make_dataclass('siteConfig',[(key,type(value)) for key,value in site_config.items()])
# # print(siteConfig.__dataclass_fields__['siteName'])



# from dataclasses import dataclass, field

# @dataclass(kw_only=True)
# class A:

#     def __post_init__(self):
#         print('A')

        
# @dataclass(kw_only=True)
# class B:

#     def __post_init__(self):
#         print('B')

        
# @dataclass(kw_only=True)
# class C(A,B):

#     x: str = field(default='a')

#     def __post_init__(self):
#         super().__post_init__()
#         print(type(self).__name__)

    
# print(C().__dataclass_fields__['x'])