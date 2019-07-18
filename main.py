#!/usr/bin/python3

# imports
import re
import os
import numpy as np
from PIL import Image # required for bilinear interpolation

import tifffile as tiff

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
        if thisCellMeta['xllcorner'] + thisCellMeta['ncols'] * (1/thisCellMeta['cellsize']) > maxCoord[0]:
            maxCoord[0] = thisCellMeta['xllcorner'] + thisCellMeta['ncols'] * thisCellMeta['cellsize']
        
        # find the extreme y-coordinates
        if thisCellMeta['yllcorner'] < minCoord[1] or minCoord[1] == -1:
            minCoord[1] = thisCellMeta['yllcorner']
        if thisCellMeta['yllcorner'] + thisCellMeta['nrows'] * (1/thisCellMeta['cellsize']) > maxCoord[1]:
            maxCoord[1] = thisCellMeta['yllcorner'] + thisCellMeta['nrows'] * thisCellMeta['cellsize']
        
        # check NaN value
        if noValue == None:
            noValue = thisCellMeta['nodata_value']
        if thisCellMeta['nodata_value'] != noValue:
            # much more processing is required to correctly handle this case; more than I require right now
            raise ValueError('Inconsistency in ''nodata_value'', aborting.')


# find a cell scale factor
REAL_CELL_SIZE = minCellSize
CELL_SCALE = 1/minCellSize
del(minCellSize)

# convert min and max coords to NumPy shape format, bearing in mind that x and y are swapped
ARRAY_SHAPE = (round((maxCoord[1]-minCoord[1])*CELL_SCALE),round((maxCoord[0]-minCoord[0])*CELL_SCALE))

ORIGIN_COORDINATES = minCoord
del(minCoord)
del(maxCoord)

NODATA_VALUE = noValue
del(noValue)

# actually create the array to store all the data
mainArray = np.full(ARRAY_SHAPE,np.NaN)
secondArray = np.full(ARRAY_SHAPE,np.NaN)

# begin overlaying arrays
for partFilename in os.listdir(DIRECTORY):
    if partFilename.lower().endswith('.asc'): # any file that we want
        filename = DIRECTORY+'/'+partFilename
        thisCellMeta = getAscMeta(open(filename, 'r'))
        thisArray = np.loadtxt(filename,skiprows=6)
        thisArray[thisArray==thisCellMeta['nodata_value']] = np.nan
        
        if thisCellMeta['cellsize'] == REAL_CELL_SIZE: # no preprocessing needed for arrays of the highest accuracy
            
            # get offset coordinates
            thisArrayOffset = (int(ARRAY_SHAPE[0]-(thisCellMeta['yllcorner']-ORIGIN_COORDINATES[1])*CELL_SCALE-thisArray.shape[1]),int((thisCellMeta['xllcorner']-ORIGIN_COORDINATES[0])*CELL_SCALE)) # very complicated code to find position of new array
            
            # actually superimpose the array
            mainArray[thisArrayOffset[0]:thisArrayOffset[0]+int(thisArray.shape[1]),thisArrayOffset[1]:thisArrayOffset[1]+int(thisArray.shape[0])] = thisArray  # this should be neater
        
        else: # for other cases, the cell is less authoritative, so put it into the secondary array
            
            # use image processing to resize our array using BILINEAR NEIGHBOUR interpolation
            newSizeX = int(thisArray.shape[1]*(thisCellMeta['cellsize']/REAL_CELL_SIZE))
            newSizeY = int(thisArray.shape[0]*(thisCellMeta['cellsize']/REAL_CELL_SIZE))
            thisArray = np.array(Image.fromarray(thisArray).resize((newSizeX,newSizeY),resample=Image.BILINEAR))
            thisArray[thisArray==thisCellMeta['nodata_value']] = np.nan

            # get offset coordinates
            thisArrayOffset = (int(ARRAY_SHAPE[0]-(thisCellMeta['yllcorner']-ORIGIN_COORDINATES[1])*CELL_SCALE-thisArray.shape[1]),int((thisCellMeta['xllcorner']-ORIGIN_COORDINATES[0])*CELL_SCALE)) # very complicated code to find position of new array
            
            # actually superimpose the array
            secondArray[thisArrayOffset[0]:thisArrayOffset[0]+int(thisArray.shape[1]),thisArrayOffset[1]:thisArrayOffset[1]+int(thisArray.shape[0])] = thisArray  # this should be neater

# eliminate NaNs (don't take too personally)
count1=0
count2=0
count3=0
for x in range(0,ARRAY_SHAPE[0]):
    for y in range(0,ARRAY_SHAPE[1]):
        if np.isnan(mainArray[x,y]): # this is the only case in which we take action
            # attempt interpolation...
            '''if x > 0 and x < ARRAY_SHAPE[0]-1 and y > 0 and y < ARRAY_SHAPE[1]-1: # ...unless the cell is around the edge
                if  not np.isnan(np.prod(mainArray[x-1:x+1,y-1]) * np.prod(mainArray[x-1:x+1,y+1]) * mainArray[x-1,y] * mainArray[x+1,y]): # if no surrounding element is zero, we can use an "implementation" of "bilinear interpolation"
                    # my implementation of biliniear interpolation may be foolishly called "finding the mean" by others...
                    mainArray[x,y] = np.nanmean(mainArray[x-1:x+1,y-1:y+1])
                    count1 += 1
            # it would be nice to add an interpolation method for the edge values at this point ''' # this was not ever running, albeit massively slowing down code execution by doind compicated multiplication
            
            # find missing data from less authoritative sources (ie. less detailed arrays)
            if not np.isnan(secondArray[x,y]):
                mainArray[x,y] = secondArray[x,y]
                count2 += 1 # for debugging
            # otherwise... I want to know about it!
            else:
                count3 += 1 # for debugging

# store extreme heights before we lose the information
MAXIMUM_HEIGHT = np.nanmax(mainArray)
MINIMUM_HEIGHT = np.nanmin(mainArray)

# normalize the heights into 16 bits
mainArray -= MINIMUM_HEIGHT # we want to use as much entropy as possible!
mainArray = (mainArray*65535/(MAXIMUM_HEIGHT-MINIMUM_HEIGHT)).astype(np.uint16) # spread the values evenly across 65536 integers and convert to uint16

np.amax(mainArray)

# write to a test file for debugging
f = open('output.raw', 'wb')
f.write(mainArray.tobytes()) # write it in a binary file
f.close()

# also write tiff for debugging
tiff.imwrite('output.tiff',mainArray)


# tell the user import settings for Unity
print('Bit depth: Bit 16') # future: add 8-bit support?
print('Width:', ARRAY_SHAPE[0])
print('Height:', ARRAY_SHAPE[1])
print('Byte order: Windows')
print('Flip vertically: No')
print('Terrain size: '+str(ARRAY_SHAPE[0]*REAL_CELL_SIZE)+'x'+str(ARRAY_SHAPE[1]*REAL_CELL_SIZE)+'x'+str(MAXIMUM_HEIGHT-MINIMUM_HEIGHT)) # for user convenience
print('Terrain Z position:', MINIMUM_HEIGHT)