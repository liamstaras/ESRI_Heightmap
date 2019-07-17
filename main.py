# imports
import re
import os
import numpy as np

### phase 1 - reading i

DIRECTORY = 'Temp/LiDAR'

# takes in an open file object, and reads the first 6 lines to give an array of the metadata
def getAscMeta(fileObj):
    # borrowed from BlenderGIS, no license included; replace with own code.
    meta_re = re.compile(r'^([^\s]+)\s+([^\s]+)$')
    meta = {}
    for i in range(6):
        line = fileObj.readline()
        m = meta_re.match(line)
        if m:
            meta[m.group(1).lower()] = float(m.group(2))
    return meta

# finds the extremes of the dimensions of all *.asc files in the directory
minCellSize = 0
minCoord = [-1,-1]
maxCoord = [0,0]
noValue = None # also look for NaN value; check consistency accross data

for filename in os.listdir(DIRECTORY):
    if filename.lower().endswith('.asc'): # any file that we want
        thisCellMeta = getAscMeta(open(DIRECTORY+'/'+filename, 'r'))

        # find the minimum cell size
        if thisCellMeta['cellsize'] < minCellSize or minCellSize == 0:
            minCellSize = thisCellMeta['cellsize']
        
        # find the extreme x-coordinates
        if thisCellMeta['xllcorner'] < minCoord[0] or minCoord[0] == -1:
            minCoord[0] = thisCellMeta['xllcorner']
        elif thisCellMeta['xllcorner'] + thisCellMeta['ncols'] * thisCellMeta['cellsize'] > maxCoord[0]:
            maxCoord[0] = thisCellMeta['xllcorner'] + thisCellMeta['ncols'] * thisCellMeta['cellsize']
        
        # find the extreme y-coordinates
        if thisCellMeta['yllcorner'] < minCoord[1] or minCoord[1] == -1:
            minCoord[1] = thisCellMeta['yllcorner']
        elif thisCellMeta['yllcorner'] + thisCellMeta['nrows'] * thisCellMeta['cellsize'] > maxCoord[1]:
            maxCoord[1] = thisCellMeta['yllcorner'] + thisCellMeta['nrows'] * thisCellMeta['cellsize']
        
        # check NaN value
        if noValue == None:
            noValue = thisCellMeta['nodata_value']
        elif thisCellMeta['nodata_value'] != noValue:
            # much more processing is required to correctly handle this case; more than I require right now
            raise ValueError('Inconsistency in ''nodata_value'', aborting.')


# find desired array dimensions from min and max coords, in NumPy tuple format
ARRAY_SHAPE = tuple(round(m-n) for m,n in zip(maxCoord,minCoord))

# redefine other useful variables as constants
REAL_CELL_SIZE = minCellSize
del(minCellSize)

ORIGIN_COORDINATES = minCoord
del(minCoord)
del(maxCoord)

NODATA_VALUE = noValue
del(noValue)

# actually create the array to store all the data
mainArray = np.full(ARRAY_SHAPE,NODATA_VALUE)
print(mainArray[0,0])