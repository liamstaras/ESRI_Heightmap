# more functions from the package

import numpy as np
from PIL import Image

## resizes a NumPy array by a given scale factor
def arrayResize(array,scale):
        newSizeX = int(array.shape[1]*scale)
        newSizeY = int(array.shape[0]*scale)
        return np.array(Image.fromarray(array).resize((newSizeX,newSizeY),resample=Image.BILINEAR))

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
    return primaryArray

## use given number of bits for array, losing distrubution information
def normalizeArray(array,bitDepth):
    # normalize the heights into _bitDepth_ integers
    array -= np.nanmin(array) # we want to use as much entropy as possible!
    array = (array*(2**bitDepth)/np.nanmax(array)).astype(np.uint16) # spread the values evenly across _bitDepth_ integers and convert to uint16
    return array

## tifffile wrapper
def exportTiff(normalizedArray,file):
    try:
        import tifffile as tiff # optional dependency
        tiff.imwrite(file,normalizedArray)
    except ImportError:
        print('tifffile required for tiff export')
        raise

## NumPy file export wrapper
def exportRAW(normalizedArray,file):
    f = open(file,'wb')
    f.write(normalizedArray.tobytes()) # write it to a binary file
    f.close()