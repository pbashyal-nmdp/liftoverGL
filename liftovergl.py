#!/usr/bin/env python3
"""
pyliftgl.py

copyright
    Bob Milius, PhD
    31 March 2017
    National Marrow Donor Program/Be The Match

Lifts over a GL String from one version of the IMGT/HLA database to another.

This program uses the Allelelist_history.txt file from
https://github.com/ANHIG/IMGTHLA

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
"""

import argparse
import json
import pandas as pd
import re
import requests
import sys

# sample data
G1 = ("HLA-A*02:06:01:01+HLA-A*11:01:01:01^"
      "HLA-B*15:01:01:01+HLA-B*35:01:01:02^"
      "HLA-C*03:02:02:01+HLA-C*04:01:01:01^"
      "HLA-DPA1*02:02:02^"
      "HLA-DPB1*05:01:01^"
      "HLA-DQA1*03:01:01^"
      "HLA-DQB1*03:02:01^"
      "HLA-DRB1*04:03:01+HLA-DRB1*04:06:01^"
      "HLA-DRB4*01:03:01:03")
S1 = "3.22.0"
T1 = "3.25.0"

G2 = ("HLA-A*02:06:01:01+HLA-A*11:01:01:01/HLA-A*32:74^"
      "HLA-B*15:01:01:01+HLA-A*32:74+HLA-B*35:01:01:02^"
      "HLA-C*03:02:02:01+HLA-C*04:01:01:01~HLA-A*32:74^"
      "HLA-DPA1*02:02:02^HLA-DPB1*05:01:01^HLA-A*32:74^"
      "HLA-DQA1*03:01:01^HLA-DQB1*03:02:01^HLA-A*32:74+HLA-A*32:74^"
      "HLA-DRB1*04:03:01/HLA-A*32:74/HLA-A*32:74/HLA-DRB1*04:06:01^"
      "HLA-DRB4*01:03:01:03")
S2 = "3.22.0"
T2 = "3.0.0"

G3 = ("HLA-A*01:01:01:01/HLA-A*01:02+HLA-A*24:03:01")
S3 = "3.20.0"
T3 = "3.25.0"

G4 = ("HLA-A*23:69^HLA-DRB1*11:11:02+HLA-DRB1*08:01:03")
S4 = "3.20.0"
T4 = "3.25.0"


def read_history():
    """
    reads the Allelelist_history.txt file that was downloaded from
    https://github.com/ANHIG/IMGTHLA
    into a pandas dataframe.
    """
    history = pd.read_csv("Allelelist_history.txt",
                          sep="\t", header=0, index_col=0, dtype=str)
    return history


def mk_glids(glstring, version, history):
    """
    takes a GL String containing allele names for a version of
    the IMGT/HLA database, and returns a GL String with HLA_IDs
    substituted for the allele names
    """
    # the history file strips the '.' from the version, and pads the
    # middle field to two spaces,
    # so '3.1.0' becomes '3010'
    v = version.split(".")
    vers = ''.join([v[0], v[1].zfill(2), v[-1]])
    for allele in get_alleles(glstring):
        hla_id = history[history[vers] == allele[4:]].index.tolist()
        if len(hla_id) == 1:
            glstring = glstring.replace(allele, hla_id[0])
        elif len(hla_id) == 0:
            print(allele, "does not exist in IMGT/HLA ver", version)
            sys.exit()
        else:
            print(allele, "has more than one id:", hla_id)
            sys.exit()
    # glstring = gl_clean(glstring)
    return glstring


def mk_target(gl_ids, target, history):
    """
    takes a GL String made up of HLA_IDs, and converts it to
    one containing allele names for a specific IMGT/HLA version
    """
    # the history file strips the '.' from the version, and pads the
    # middle field to two spaces,
    # so '3.1.0' becomes '3010'
    t = target.split(".")
    targ = ''.join([t[0], t[1].zfill(2), t[-1]])
    target_gl = gl_ids
    for hla_id in get_alleles(gl_ids):
        new_allele = "HLA-" + str(history[targ][hla_id])
        target_gl = target_gl.replace(hla_id, new_allele)
    target_gl = gl_clean(target_gl)
    return target_gl


def gl_clean(glstring):
    """
    takes a GL String that has just been lifted to another version,
    and removes deleted alleles, and cleans up resulting
    delimiters left behind
    """
    # remove non-existant alleles
    glstring = glstring.replace("HLA-nan", "")
    # after deleting the above, delimiters may be packed together. These have
    # to removed when they are at the beginning or end of the GL String, or
    # resolved to the highest precedence when they are in the middle of the
    # GL String
    # ---
    # trailing delimiters
    glstring = re.sub(r'[/~+|^]+$', '', glstring)
    # leading delimiters
    glstring = re.sub(r'^[/~+|^]+', '', glstring)
    # the rest in order of precedence
    glstring = re.sub(r'[/~+|^]*\^[/~+|^]*', '^', glstring)
    glstring = re.sub(r'[/~+|]*\|[/~+|]*', '|', glstring)
    glstring = re.sub(r'[/~+]*\+[/~+]*', '+', glstring)
    glstring = re.sub(r'[/~]*\~[/+]*', '~', glstring)
    glstring = re.sub(r'\/+', '/', glstring)
    return glstring


def get_alleles(glstring):
    """
    Takes a GL String, and returns a set containing all the alleles
    """
    alleles = set()
    for allele in re.split(r'[/~+|^]', glstring):
        alleles.add(allele)
    return alleles


def get_resource(glstring):
    """
    takes a GL String, and returns the resource type based on which
    delimiters are present
    """
    if '^' in glstring:
        return "multilocus-unphased-genotype"
    elif '|' in glstring:
        return "genotype-list"
    elif '+' in glstring:
        return "genotype"
    elif '~' in glstring:
        return "haplotype"
    elif "/" in glstring:
        return "allele-list"
    else:
        return "allele"


def post_gl(glstring, version, resource):
    """
    takes a GL String and version, and posts it to the gl.nmdp.org
    and returns a dictionary containing the status code, the
    response text, and the response location if successful
    """
    url = 'http://gl.nmdp.org/imgt-hla/' + version + "/" + resource
    headers = {'content-type': 'plain/text'}
    response = requests.post(url, data=glstring, headers=headers)
    if response.status_code == 201:
        return {'status_code': response.status_code,
                'text': response.text,
                'location': response.headers['location']}
    else:
        return {'status_code': response.status_code,
                'text': response.text}


def get_gl(uri):
    response = requests.get(uri)
    return response


def build_output(s_response, t_response):
    output = {
        "source_gl": s_response['text'],
        "source_uri": s_response['location'],
        "target_gl": t_response['text'],
        "target_uri": t_response['location'],
    }
    return output


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-g", "--glstring",
                       help="GL String to be converted",
                       type=str)
    group.add_argument("-u", "--uri",
                       help="GL Service URI of GL String",
                       type=str)
    parser.add_argument("-s", "--source",
                        required=True,
                        help="Source IMGT/HLA version",
                        type=str)
    parser.add_argument("-t", "--target",
                        help="Target IMGT/HLA version",
                        default="3.25.0",
                        type=str)
    args = parser.parse_args()

    args = parser.parse_args()
    if (args.glstring is None) and (args.uri is None):
        parser.error("at least one of --glstring or --uri required")

    s_uri = args.uri
    gl = args.glstring
    source = args.source
    target = args.target

    if s_uri:
        resource = s_uri.split('/')[-2]
        response = get_gl(s_uri)
        if response.status_code == 200:
            gl = response.text
        else:
            print("status_code =", response.status_code)
            print("text =", response.text)
            sys.exit()
    if gl:
        resource = get_resource(gl)

    history = read_history()
    print("gl =", gl)
    print("source =", source)
    print("target =", target)
    gl_ids = mk_glids(gl, source, history)
    print("IDs =", gl_ids, "\n")
    target_gl = mk_target(gl_ids, target, history)
    if not target_gl:
        print("empty target GL String, all alleles dropped")
        sys.exit()
    print("target GL =", target_gl, "\n")
    s_response = post_gl(gl, source, resource)
    print("source location =", s_response['text'], "\n")
    t_response = post_gl(target_gl, target, resource)
    output = json.dumps(build_output(s_response, t_response),
                        sort_keys=True, indent=4)
    print(output)


if __name__ == "__main__":
    main()
