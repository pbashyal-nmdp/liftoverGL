liftovergl.py
=============
tested with Python 3.6

Usage
-----
::

   liftovergl.py --help
   usage: liftovergl.py [-h] [-g GLSTRING | -u URI | -j JFILE] [-s SOURCE] [-t TARGET]

   optional arguments:
     -h, --help                          show this help message and exit
     -g GLSTRING, --glstring GLSTRING    GL String to be converted
     -u URI, --uri URI                   GL Service URI of GL String
     -f JFILE, --jfile JFILE             input file containing JSON
     -s SOURCE, --source SOURCE          Source IMGT/HLA version, e.g., '3.0.0'
     -t TARGET, --target TARGET          Target IMGT/HLA version, e.g. '3.25.0'
  
Any of the following may be used for input:

- GLSTRING : GL String 
- URI : URI pointing to a GL String, 
- JFILE : JSON input file containing the URI and source and target namespaces

| If GLSTRING is specified, TARGET and SOURCE also need to be specified
| If URI is specified, only TARGET needs to be specified since SOURCE is obtained from the URI 
| If JFILE is specified, TARGET and SOURCE do not need to be specified since they are both contained in the JSON input file.
| 

The JFILE input file uses the same JSON format used by the liftover service (https://gl.nmdp.org/liftover/)

Example JFILE input file:: 

  {
      sourceNamespace: https://gl.nmdp.org/imgt-hla/3.20.0/,
      sourceUri: https://gl.nmdp.org/imgt-hla/3.20.0/genotype/2i4,
      targetNamespace: https://gl.nmdp.org/imgt-hla/3.25.0/
  }


Description
-----------
Converts a GL String from one version of the IMGT/HLA database to another.

The program returns JSON formated output: ::

  {
      sourceGl: "input GL String to be converted" 
      sourceUri: "URI of GL String registered in a GL service" 
      targetGl: "GL String converted to a different IMGT/HLA version"
      targetUri: "URI of converted GL String"
  }

This program uses a ``AllelelistGgroups_history.txt`` file which was created by
combining data from ``Allelelist_history.txt``, ``hml_ambigs.xml``, and 
``hla_nom_g.txt`` files from https://github.com/ANHIG/IMGTHLA. The 
``AllelelistGgroups_history.txt`` will need to regenerated every time a 
new version of the IMGT/HLA database is released.

| Alleles and G-groups are converted to HLA and HGG IDs, respectively, and 
then mapped directly to alleles
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

Requirements:
------------
::

  #!/usr/bin/env python3
  import argparse
  import json
  import pandas
  import re
  import requests
  import sys


Examples
--------
Using a GL String for input::

   ./liftovergl.py -g "HLA-A*01:01:01:01/HLA-A*01:02+HLA-A*24:03:01" -s '3.20.0' -t '3.25.0'
   {
       "sourceGl": "HLA-A*01:01:01:01/HLA-A*01:02+HLA-A*24:03:01",
       "sourceUri": "https://gl.nmdp.org/imgt-hla/3.20.0/genotype/2i4",
       "targetGl": "HLA-A*01:01:01:01/HLA-A*01:02+HLA-A*24:03:01:01",
       "targetUri": "https://gl.nmdp.org/imgt-hla/3.25.0/genotype/p9"
   }

Using a URI for input::

   ./liftovergl.py -u "https://gl.nmdp.org/imgt-hla/3.20.0/genotype/2i4" -t '3.25.0'
   {
       "sourceGl": "HLA-A*01:01:01:01/HLA-A*01:02+HLA-A*24:03:01",
       "sourceUri": "https://gl.nmdp.org/imgt-hla/3.20.0/genotype/2i4",
       "targetGl": "HLA-A*01:01:01:01/HLA-A*01:02+HLA-A*24:03:01:01",
       "targetUri": "https://gl.nmdp.org/imgt-hla/3.25.0/genotype/p9"
   }

Using a JSON file with the example above for input::

   ./liftovergl.py -f genotype.json 
   {
       "sourceGl": "HLA-A*01:01:01:01/HLA-A*01:02+HLA-A*24:03:01",
       "sourceUri": "https://gl.nmdp.org/imgt-hla/3.20.0/genotype/2i4",
       "targetGl": "HLA-A*01:01:01:01/HLA-A*01:02+HLA-A*24:03:01:01",
       "targetUri": "https://gl.nmdp.org/imgt-hla/3.25.0/genotype/p9"
   }

In the following example containing four alleles, three get dropped going from ``3.18.0`` to ``3.25.0``,
and another's name is changed from ``HLA-A*26:03:02`` to ``HLA-A*26:111`` :: 

   ./liftovergl.py -g 'HLA-A*03:194+HLA-A*26:03:02^HLA-DRB1*11:11:02+HLA-DRB1*08:01:03' -s "3.18.0" -t "3.25.0"
   {
       "sourceGl": "HLA-A*03:194+HLA-A*26:03:02^HLA-DRB1*11:11:02+HLA-DRB1*08:01:03",
       "sourceUri": "https://gl.nmdp.org/imgt-hla/3.18.0/multilocus-unphased-genotype/k",
       "targetGl": "HLA-A*26:111",
       "targetUri": "https://gl.nmdp.org/imgt-hla/3.25.0/multilocus-unphased-genotype/uw"
   }

Same as above, but added ``HLA-B`` locus::

   ./liftovergl.py -g 'HLA-A*03:194+HLA-A*26:03:02^HLA-B*40:10:01+HLA-B*44:03:01/HLA-B*44:03:02^HLA-DRB1*11:11:02+HLA-DRB1*08:01:03' -s "3.18.0" -t "3.25.0"
   {
       "sourceGl": "HLA-A*03:194+HLA-A*26:03:02^HLA-B*40:10:01+HLA-B*44:03:01/HLA-B*44:03:02^HLA-DRB1*11:11:02+HLA-DRB1*08:01:03",
       "sourceUri": "https://gl.nmdp.org/imgt-hla/3.18.0/multilocus-unphased-genotype/m",
       "targetGl": "HLA-A*26:111^HLA-B*40:10:01:01+HLA-B*44:03:01:01/HLA-B*44:03:02",
       "targetUri": "https://gl.nmdp.org/imgt-hla/4.25.0/multilocus-unphased-genotype/uy"
   }

multilocus-unphased-genotype containing a G-group::

   ./liftovergl.py -f mugG.json
   {
      "sourceGl": "HLA-A*01:01:01G+HLA-A*26:03:02^HLA-B*40:10:01+HLA-B*44:03:01/HLA-B*44:03:02",
      "sourceUri": "https://gl.nmdp.org/imgt-hla/3.18.0/multilocus-unphased-genotype/n",
      "targetGl": "HLA-A*01:01:01G+HLA-A*26:111^HLA-B*40:10:01:01+HLA-B*44:03:01:01/HLA-B*44:03:02",
      "targetUri": "https://gl.nmdp.org/imgt-hla/3.25.0/multilocus-unphased-genotype/uz"
   }
