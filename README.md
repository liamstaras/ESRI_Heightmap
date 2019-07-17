# ESRI_Heightmap
Convert an ESRI Grid ASCII (*.asc) file to a RAW heightmap

# Functions of the code:
main.py processes data in a *.asc file to give a heatmap as a RAW (*.tiff) file though the following process:
1) Reads authoritative *.asc files into NumPy array with respect to coordinates.
2) Replaces all NaN values with those from less authoritative arrays if available.
3) Interpolates to find still missing values.

Detailed breakdown:
1) Reading
(i) Find coordinates to work from
    (a) Find minimum coordinates across all files.
    (b) Find difference between these and the maximum coordinates.
    (c) Define array from vector of coorinate difference (tuple?)
  or
    (a) Ask user for coordinate range
(ii) Actually read in data from most authoritative arrays, overlaying.
(iii) Ascertain NaN value.

2) Reading 2
(i) Loop through all data points and find NaNs.
(ii) Match NaNs with equivalent points in less authoritative array and replace if number exists.

3) Interpolating
(i) Check for remaining NaNs.
(ii) Repalce NaNs with mean of eight surrounding points (diagonals count as 0.5 weighting [or 1/sqrt(2) for more accuracy?])