# contains the command line application
from . import * # run __init__.py script

import argparse # running as application, so arguments very important
import os # misc directory functions
import numpy as np # important for arrays!

parser = argparse.ArgumentParser(description='Process *.asc files into an image heightmap',prog='python -m esri_heightmap')
parser.add_argument('path_to_input', type=str, help='path to *.asc file or directory containing *.asc files on which to run processing')
parser.add_argument('path_to_output', type=str, help='path to output file without extension')
parser.add_argument('--output_mode', type=str, choices=['RAW','TIFF','BOTH'], default='TIFF', help='output file format (default: BOTH)')
parser.add_argument('--directory', help='run the process on a directory of *.asc files', action='store_true')
args = parser.parse_args()

if args.directory: # different code for multiple files
    minCellSize = 0
    minCoord = [-1,-1]
    maxCoord = [0,0]

    # looping through all files in the directory
    for partFilename in os.listdir(args.path_to_input):
        if partFilename.lower().endswith('.asc'): # any file that we want
            filename = args.path_to_input+'/'+partFilename
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
    for partFilename in os.listdir(args.path_to_input):
        if partFilename.lower().endswith('.asc'): # any file that we want
            filename = args.path_to_input+'/'+partFilename
            thisAscMeta = getAscMeta(open(filename, 'r'))
            thisArray = np.loadtxt(filename,skiprows=6)
            overlayArrays(mainArray,ORIGIN_COORDINATES,thisArray,thisAscMeta,REAL_CELL_SIZE)

else:
    mainArray = np.loadtxt(args.path_to_input,skiprows=6) # no need for any fancy overlaying!
    secondArray = None

# eliminate NaNs (don't take too personally!)
eliminateNoData(mainArray,secondArray)

# store extreme heights before we lose the information
MAXIMUM_HEIGHT = np.nanmax(mainArray)
MINIMUM_HEIGHT = np.nanmin(mainArray)

# IPOS Model - output necessary!
normalizedArray = normalizeArray(mainArray,16)
if args.output_mode == 'TIFF':
    exportTiff(normalizedArray,args.path_to_output+'.tiff')
elif args.output_mode == 'RAW':
    exportRAW(normalizedArray, args.path_to_output+'.raw')
else:
    exportTiff(normalizedArray, args.path_to_output+'.tiff')
    exportRAW(normalizedArray, args.path_to_output+'.raw')