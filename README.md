# Kieran Cyphus Thesis

## Guide to files
Anything prefixed by `experiment_` are files that are meant to be run to create graphs / values and arrays that are
used in the other files

The remainder of the files are components of the system that actually convert a given network into an IWN.

###`FileParser.py`:
Converts existing inp files into their iwn equivalents.

`--file`: path to .inp file to be converted to iwn

`--output`: filepath to the output file

