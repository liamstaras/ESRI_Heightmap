#!/usr/bin/python3

## ESRI_Heighmap - Python code to process ESRI data into the form of a Unity-style heightmap for the creation of 3d objects

### NOTICE ###
## If editing this code, there are a few things to bear in mind:
# 1) NumPy array indexing SWAPS X AND Y - this caused many problems in the early stages of software development.
# 2) My code is not in ANY WAY the best algorithmic solution to the problems layed out. If it is, then this is probably a coincidence.
# 3) The method for importing and exporting data is currently very clunky. The path to a folder of *.asc files is defined below as the constant DIRECTORY and the output is a *.tif and *.raw file, each containing the same data.

# terminonogy:
# cell = a single part of a grid square

## imports
import re # for getAscMeta
import os # for directory listings
import numpy as np # for most other things
from PIL import Image # required for bilinear interpolation function used to upscale low-res cells

import tifffile as tiff # for producing a normal tiff file for debugging and showing off the code, not required in production version

DIRECTORY = 'Temp/LiDAR' # defined as constant for now; could be parameter in final function?

## takes in an open file object, and reads the first 6 lines to give an array of the metadata at the top - used extensively throughout program

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

## Finds the extremes of the dimensions of all *.asc files in the directory

minCellSize = 0
minCoord = [-1,-1]
maxCoord = [0,0]

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

## define some useful constants

# find a cell scale factor
REAL_CELL_SIZE = minCellSize
CELL_SCALE = 1/minCellSize
del(minCellSize)

# convert min and max coords to NumPy shape format, bearing in mind that x and y are swapped
ARRAY_SHAPE = (round((maxCoord[1]-minCoord[1])*CELL_SCALE),round((maxCoord[0]-minCoord[0])*CELL_SCALE))

ORIGIN_COORDINATES = minCoord
del(minCoord)
del(maxCoord)

## actually import the data into NumPy

# create the arrays to store all the data
mainArray = np.full(ARRAY_SHAPE,np.NaN)
secondArray = np.full(ARRAY_SHAPE,np.NaN) # a slightly hacky solution of offloading less preferable data to a second array, and then remerging later - could be replaced

# begin overlaying arrays
for partFilename in os.listdir(DIRECTORY):
    if partFilename.lower().endswith('.asc'): # any file that we want
        
        # these next few steps should be carried out regardless of the resolution of the cell
        filename = DIRECTORY+'/'+partFilename
        thisCellMeta = getAscMeta(open(filename, 'r'))
        thisArray = np.loadtxt(filename,skiprows=6)
        thisArray[thisArray==thisCellMeta['nodata_value']] = np.nan
        
        if thisCellMeta['cellsize'] == REAL_CELL_SIZE: # select the highest resolution cells; these do not need preprocessing and are stored straight into the main array
            
            # get offset coordinates - where to superimpose the array
            thisArrayOffset = (int(ARRAY_SHAPE[0]-(thisCellMeta['yllcorner']-ORIGIN_COORDINATES[1])*CELL_SCALE-thisArray.shape[1]),int((thisCellMeta['xllcorner']-ORIGIN_COORDINATES[0])*CELL_SCALE)) # very complicated code to find position of new array
            
            # perform the superimposition (*fancyword*)
            mainArray[thisArrayOffset[0]:thisArrayOffset[0]+int(thisArray.shape[1]),thisArrayOffset[1]:thisArrayOffset[1]+int(thisArray.shape[0])] = thisArray  # this should be neater
        
        else: # for other cases, the cell is less authoritative, so put it into the secondary array
            
            # use image processing to resize our array using BILINEAR NEIGHBOUR interpolation
            newSizeX = int(thisArray.shape[1]*(thisCellMeta['cellsize']/REAL_CELL_SIZE))
            newSizeY = int(thisArray.shape[0]*(thisCellMeta['cellsize']/REAL_CELL_SIZE))
            thisArray = np.array(Image.fromarray(thisArray).resize((newSizeX,newSizeY),resample=Image.BILINEAR))

            # get offset coordinates
            thisArrayOffset = (int(ARRAY_SHAPE[0]-(thisCellMeta['yllcorner']-ORIGIN_COORDINATES[1])*CELL_SCALE-thisArray.shape[1]),int((thisCellMeta['xllcorner']-ORIGIN_COORDINATES[0])*CELL_SCALE)) # very complicated code to find position of new array
            
            # superimpose the array
            secondArray[thisArrayOffset[0]:thisArrayOffset[0]+int(thisArray.shape[1]),thisArrayOffset[1]:thisArrayOffset[1]+int(thisArray.shape[0])] = thisArray  # this should be neater

# eliminate NaNs (don't take too personally)
for x in range(0,ARRAY_SHAPE[0]):
    for y in range(0,ARRAY_SHAPE[1]):
        if np.isnan(mainArray[x,y]): # this is the only case in which we take action
            
            # there once lived here a simple interpolation function to eliminate "dead pixels" - this has since been removed as it slowed down the code and had no effect whatsoever in 99% of cases [citation needed]
            
            # find missing data from less authoritative sources (ie. less detailed arrays) ONLY if that data is not a NaN
            if not np.isnan(secondArray[x,y]):
                mainArray[x,y] = secondArray[x,y]
            # at this point, an else should be added to peform some kind of interpolaion patchwork for remaining NaNs

# something should be done about large areas with no data about here

# store extreme heights before we lose the information
MAXIMUM_HEIGHT = np.nanmax(mainArray)
MINIMUM_HEIGHT = np.nanmin(mainArray)

# normalize the heights into 16 bits - in future add an 8 bit option?
mainArray -= MINIMUM_HEIGHT # we want to use as much entropy as possible!
mainArray = (mainArray*65535/(MAXIMUM_HEIGHT-MINIMUM_HEIGHT)).astype(np.uint16) # spread the values evenly across 65536 integers and convert to uint16

# write to a test file for debugging
f = open('output.raw', 'wb')
f.write(mainArray.tobytes()) # write it in a binary file
f.close()

# also write tiff for debugging
tiff.imwrite('output.tiff',mainArray)


# tell the user import settings for Unity - convert to more standard format in future to support more applications
# Unity is not playing ball with files of resolution greater than 4096x4096 - BIG PROBLEM
print('Bit depth: Bit 16') # future: add 8-bit support?
print('Width:', ARRAY_SHAPE[0])
print('Height:', ARRAY_SHAPE[1])
print('Byte order: Windows')
print('Flip vertically: No')
print('Terrain size: '+str(ARRAY_SHAPE[0]*REAL_CELL_SIZE)+'x'+str(ARRAY_SHAPE[1]*REAL_CELL_SIZE)+'x'+str(MAXIMUM_HEIGHT-MINIMUM_HEIGHT)) # for user convenience
print('Terrain Z position:', MINIMUM_HEIGHT) # this is for users wanting to use multiple terrains and import them into a single world