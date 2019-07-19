import numpy as np
from PIL import Image
import re
import tifffile

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

## resizes a NumPy array by a given scale factor
def arrayResize(array,scale):
        newSizeX = int(array.shape[1]*scale)
        newSizeY = int(array.shape[0]*scale)
        return np.array(Image.fromarray(array).resize((newSizeX,newSizeY),resample=Image.BILINEAR))


## superimposes an asc array onto a primary array using metadata
def overlayCell(mainArray, originOffset, newArray, ascMeta, finalResolution):            
    newArray[newArray==ascMeta['nodata_value']] = np.nan # eliminate nodata_value into nice NaNs
    
    if ascMeta['cellsize'] != finalResolution: # if cell size is different, we must resize
        newArray = arrayResize(ascMeta,ascMeta['cellsize']/finalResolution)
        
    # get offset coordinates - where to superimpose the array
    newArrayOffset = (int(mainArray.shape[0]-(ascMeta['yllcorner']+originOffset[1])*(1/finalResolution)-newArray.shape[1]),int((ascMeta['xllcorner']+originOffset[0])*(1/finalResolution))) # very complicated code to find position of new array
    
    # perform the superimposition (*fancyword*)
    mainArray[newArrayOffset[0]:newArrayOffset[0]+int(newArray.shape[1]),newArrayOffset[1]:newArrayOffset[1]+int(newArray.shape[0])] = newArray  # this should be neater


## eliminates NaNs (don't take too personally) by attempting to find data in secondary array (data of lower resolution) and other methods (_future_)
# there may be a NumPy function to do this already (I couldn't find one) - if there is, please use it instead OR update the source and create a pull request OR tell me!
def NaNReplace(primaryArray,secondaryArray):
    for x in range(0,primaryArray.shape[0]):
        for y in range(0,primaryArray.shape[1]):
            if np.isnan(primaryArray[x,y]): # this is the only case in which we take action         
                # there once lived here a simple interpolation function to eliminate "dead pixels" - this has since been removed as it slowed down the code and had no effect whatsoever in 99% of cases [citation needed]
                
                # find missing data from less authoritative sources (ie. less detailed arrays) ONLY if that data is not a NaN
                if not np.isnan(secondaryArray[x,y]):
                    primaryArray[x,y] = secondaryArray[x,y]
                # at this point, an "else" clause should be added to peform some kind of interpolaion patchwork for remaining NaNs


## convert array to given number of bits, losing distrubution information
def normalizeArray(array,bitDepth):
    # normalize the heights into 16 bits - in future add an 8 bit option?
    array -= np.nanmin(array) # we want to use as much entropy as possible!
    array = (array*(2**bitDepth)/np.nanmax(array)).astype(np.uint16) # spread the values evenly across 65536 integers and convert to uint16
    return array