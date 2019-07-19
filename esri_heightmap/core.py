import numpy as np
from .helpers import *
import re

## gets the metadata from a *.asc file and returns it as a friendly dictionary object
def getAscMeta(fileObj):
    # borrowed from https://github.com/domlysz/BlenderGIS, in turn derived from https://github.com/hrbaer/Blender-ASCII-Grid-Import - no license included in either; replace with bespoke code in near future to avoid conflict
    meta_re = re.compile(r'^([^\s]+)\s+([^\s]+)$') # strange regex magic
    meta = {}
    for i in range(6):
        line = fileObj.readline()
        m = meta_re.match(line)
        if m:
            meta[m.group(1).lower()] = float(m.group(2))
    return meta

## superimposes an asc array onto a primary array using metadata
def overlayArrays(mainArray, originOffset, newArray, ascMeta, finalResolution):            
    newArray[newArray==ascMeta['nodata_value']] = np.nan # eliminate nodata_value into nice NaNs
    
    if ascMeta['cellsize'] != finalResolution: # if cell size is different, we must resize
        newArray = arrayResize(newArray,ascMeta['cellsize']/finalResolution)
        
    # get offset coordinates - where to superimpose the array
    newArrayOffset = (int(mainArray.shape[0]-(ascMeta['yllcorner']-originOffset[1])*(1/finalResolution)-newArray.shape[1]),int((ascMeta['xllcorner']-originOffset[0])*(1/finalResolution))) # very complicated code to find position of new array
    
    # perform the superimposition (*fancyword*)
    mainArray[newArrayOffset[0]:newArrayOffset[0]+int(newArray.shape[1]),newArrayOffset[1]:newArrayOffset[1]+int(newArray.shape[0])] = newArray  # this should be neater
    return mainArray

## Clear NaNs
def eliminateNoData(mainArray, secondArray):
    if secondArray != None: # if single file, secondArray will not exist, therefore interpolation is the only option
        mainArray = NaNReplace(mainArray, secondArray)
    else:
        pass # add other NaN removal code HERE ie. interpolation