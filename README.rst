liftovergl.py
=============
Usage
-----
::

   liftovergl.py --help
   usage: liftovergl.py [-h] [-g GLSTRING | -u URI] -s SOURCE [-t TARGET]
   
   optional arguments:
     -h, --help            show this help message and exit
     -g GLSTRING, --glstring GLSTRING    GL String to be converted
     -u URI,      --uri URI              GL Service URI of GL String
     -s SOURCE,   --source SOURCE        Source IMGT/HLA version
     -t TARGET,   --target TARGET        Target IMGT/HLA version
  
| Either the GLSTRING or a URI pointing to it may be used.
| If TARGET isn't supplied, it defaults to 3.25.0

Description
-----------
Converts a GL String from one version of the IMGT/HLA database to another.

This program uses the Allelelist_history.txt file from
https://github.com/ANHIG/IMGTHLA
which must be downloaded separately.

Alleles are converted to HLA accession #s, and then mapped to directly alleles
in the target version. If alleles do not exist in the target, then they are
dropped from the target GL String. Alleles are not expanded to include new
alleles. eg., the following alleles exist for 3.20.0 and 3.24.0:

| 3.20.0
| ``HLA00053``  ``HLA-A*24:03:01``
| 
| 3.24.0
| ``HLA00053``  ``HLA-A*24:03:01:01``
| ``HLA14804``  ``HLA-A*24:03:01:02``
|
| When ``HLA-A*24:03:01`` is converted from 3.20.0 to 3.25.0, it gets assigned to
| ``HLA-A*24:03:01:01``  and not
| ``HLA-A*24:03:01:01/HLA-A*24:03:01:02``

Examples
--------
::

   ./liftovergl.py -u "https://gl.nmdp.org/imgt-hla/3.20.0/genotype/2i4" -s '3.20.0' -t '3.25.0'
   {
       "source_gl": "HLA-A*01:01:01:01/HLA-A*01:02+HLA-A*24:03:01",
       "source_uri": "https://gl.nmdp.org/imgt-hla/3.20.0/genotype/2i4",
       "target_gl": "HLA-A*01:01:01:01/HLA-A*01:02+HLA-A*24:03:01:01",
       "target_uri": "https://gl.nmdp.org/imgt-hla/3.25.0/genotype/p9"
   }

::

   ./liftovergl.py -g "HLA-A*01:01:01:01/HLA-A*01:02+HLA-A*24:03:01" -s '3.20.0' -t '3.25.0'
   {
       "source_gl": "HLA-A*01:01:01:01/HLA-A*01:02+HLA-A*24:03:01",
       "source_uri": "https://gl.nmdp.org/imgt-hla/3.20.0/genotype/2i4",
       "target_gl": "HLA-A*01:01:01:01/HLA-A*01:02+HLA-A*24:03:01:01",
       "target_uri": "https://gl.nmdp.org/imgt-hla/3.25.0/genotype/p9"
   }
