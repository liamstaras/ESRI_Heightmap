# imports
import re
import os
import numpy as np

DIRECTORY = 'Temp/LiDAR' # defined as constant for now

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

## Finds the extremes of the dimensions of all *.asc files in the directory

minCellSize = 0
minCoord = [-1,-1]
maxCoord = [0,0]
noValue = None # also look for NaN value; check consistency accross data

# looping through all files in the directory
for partFilename in os.listdir(DIRECTORY):
    if partFilename.lower().endswith('.asc'): # any file that we want
        filename = DIRECTORY+'/'+partFilename
        thisCellMeta = getAscMeta(open(filename, 'r'))

        # find the minimum cell size
        if thisCellMeta['cellsize'] < minCellSize or minCellSize == 0:
            minCellSize = thisCellMeta['cellsize']
        
        # find the extreme x-coordinates
        if thisCellMeta['xllcorner'] < minCoord[0] or minCoord[0] == -1:
            minCoord[0] = thisCellMeta['xllcorner']
        elif thisCellMeta['xllcorner'] + thisCellMeta['ncols'] * (1/thisCellMeta['cellsize']) > maxCoord[0]:
            maxCoord[0] = thisCellMeta['xllcorner'] + thisCellMeta['ncols'] * thisCellMeta['cellsize']
        
        # find the extreme y-coordinates
        if thisCellMeta['yllcorner'] < minCoord[1] or minCoord[1] == -1:
            minCoord[1] = thisCellMeta['yllcorner']
        elif thisCellMeta['yllcorner'] + thisCellMeta['nrows'] * (1/thisCellMeta['cellsize']) > maxCoord[1]:
            maxCoord[1] = thisCellMeta['yllcorner'] + thisCellMeta['nrows'] * thisCellMeta['cellsize']
        
        # check NaN value
        if noValue == None:
            noValue = thisCellMeta['nodata_value']
        elif thisCellMeta['nodata_value'] != noValue:
            # much more processing is required to correctly handle this case; more than I require right now
            raise ValueError('Inconsistency in ''nodata_value'', aborting.')


# find desired array dimensions from min and max coords, in NumPy tuple format
ARRAY_SHAPE = tuple(round((m-n)*(1/minCellSize)) for m,n in zip(maxCoord,minCoord))

# redefine other useful variables as constants
REAL_CELL_SIZE = minCellSize
CELL_SCALE = 1/minCellSize
del(minCellSize)

ORIGIN_COORDINATES = minCoord
del(minCoord)
del(maxCoord)

NODATA_VALUE = noValue
del(noValue)

# actually create the array to store all the data
mainArray = np.full(ARRAY_SHAPE,np.NaN)

# begin overlaying arrays
for partFilename in os.listdir(DIRECTORY):
    if partFilename.lower().endswith('.asc'): # any file that we want
        filename = DIRECTORY+'/'+partFilename
        thisCellMeta = getAscMeta(open(filename, 'r'))
        if thisCellMeta['cellsize'] == REAL_CELL_SIZE: # we only want arrays that we aren't resizing for now
            thisArray = np.loadtxt(filename,skiprows=6)
            thisArray[thisArray==NODATA_VALUE] = np.nan # potential for variation in NODATA_value to be supported
            
            # get offset coordinates
            thisArrayOffset = (int((thisCellMeta['xllcorner']-ORIGIN_COORDINATES[0])*CELL_SCALE),int((thisCellMeta['yllcorner']-ORIGIN_COORDINATES[1])*CELL_SCALE)) # make more Pythonic?
            
            # actually superimpose the array
            #print(str(thisArrayOffset[0]) + ':' + str(thisArrayOffset[0]+int(thisCellMeta['ncols'])) + ', ' + str(thisArrayOffset[1]) + ':' + str(thisArrayOffset[1]+int(thisCellMeta['nrows']))) # uncomment for debugging!
            mainArray[thisArrayOffset[0]:thisArrayOffset[0]+int(thisCellMeta['ncols']), thisArrayOffset[1]:thisArrayOffset[1]+int(thisCellMeta['nrows'])] = thisArray  # this should be neater
