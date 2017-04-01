# pyliftover
Converts a GL String from one version of the IMGT/HLA database to another.

This program uses the Allelelist_history.txt file from
https://github.com/ANHIG/IMGTHLA
which must be downloaded separately.

Alleles are converted to HLA accession #s, and then mapped to directly alleles
in the target version. If alleles do not exist in the target, then they are
dropped from the target GL String. Alleles are not expanded to include new
alleles. eg., the following alleles exist for 3.20.0 and 3.24.0:

3.20.0
HLA00053 HLA-A*24:03:01

3.24.0
HLA00053 HLA-A*24:03:01:01
HLA14804 HLA-A*24:03:01:02

When HLA-A*24:03:01 is converted from 3.20.0 to 3.25.0, it gets assigned to
HLA-A*24:03:01:01
and not
HLA-A*24:03:01:01/HLA-A*24:03:01:02
