# ESRI_Heightmap
Convert an ESRI Grid ASCII (\*.asc) to a binary headerless TIFF (\*.raw) for use as a heightmap.

## Installation
Download the repository and Python 3. Then, run `python3 setup.py` in the directory with the code to install.

## Usage
~~~
python -m esri_heightmap [-h] [--output_mode {RAW,TIFF,BOTH}]
                              [--directory]
                              path_to_input path_to_output

Process *.asc files into an image heightmap

positional arguments:
  path_to_input         path to *.asc file or directory containing *.asc files
                        on which to run processing
  path_to_output        path to output file without extension

optional arguments:
  -h, --help            show this help message and exit
  --output_mode {RAW,TIFF,BOTH}
                        output file format (default: BOTH)
  --directory           run the process on a directory of *.asc files
~~~

## Use cases
Our use case is for getting LiDAR data into Unity as a terrain for VR interaction. Add yours here!
