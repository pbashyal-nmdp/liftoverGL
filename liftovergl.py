#!/usr/bin/env python3
"""
pyliftgl.py

copyright
    Bob Milius, PhD - 31 March 2017
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
import os
import pandas as pd
import re
import requests
import sys


def read_history():
    """
    reads the AllelelistGgroups_history.txt file that was downloaded from
    https://github.com/ANHIG/IMGTHLA
    into a pandas dataframe.
    """
    history_file = os.environ["IMGTHLA"] + "/AllelelistGgroups_history.txt"
    try:
        history = pd.read_csv(history_file,
                              sep="\t", header=0, index_col=0, dtype=str)
        return history
    except:
        print("could not read {}".format(history_file))
        sys.exit()


def mk_glids(glstring, version, history):
    """
    takes a GL String containing allele names for a version of
    the IMGT/HLA database, and returns a GL String with HLA_IDs
    substituted for the allele names
    """
    # the history file strips the '.' from the version, and pads the
    # middle field to two spaces,  so '3.1.0' becomes '3010'
    v = version.split(".")
    vers = "".join([v[0], v[1].zfill(2), v[-1]])
    for allele in get_alleles(glstring):
        hla_id = history[history[vers] == allele[4:]].index.tolist()
        if len(hla_id) == 1:
            glstring = glstring.replace(allele, hla_id[0])
        elif len(hla_id) == 0:
            print("{} does not exist in "
                    "IMGT/HLA ver {}".format(allele, version))
            sys.exit()
        else:
            print("{} has more than one id: {}".format(allele, hla_id))
            sys.exit()
    return glstring


def mk_target(gl_ids, target, history):
    """
    takes a GL String made up of HLA IDs, and converts it to
    one containing allele names for a specific IMGT/HLA version
    """
    # the history file strips the '.' from the version, and pads the
    # middle field to two spaces,  so '3.1.0' becomes '3010'
    t = target.split(".")
    targ = "".join([t[0], t[1].zfill(2), t[-1]])
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
    if "^" in glstring:
        return "multilocus-unphased-genotype"
    elif "|" in glstring:
        return "genotype-list"
    elif "+" in glstring:
        return "genotype"
    elif "~" in glstring:
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
    # url = 'http://gl.nmdp.org/imgt-hla/' + version + "/" + resource
    url = 'http://gl.nmdp.org/imgt-hla/{}/{}'.format(version, resource)
    headers = {'content-type': 'plain/text'}
    response = requests.post(url, data=glstring, headers=headers)
    if response.status_code == 201:
        return {'status_code': response.status_code,
                'text': response.text,
                'location': response.headers['location']}
    else:
        return {'status_code': response.status_code,
                'text': response.text}


def from_source_uri(source_uri):
    """
    extracts the source IMGT/HLA version and resource from the source_uri,
    then POSTs the uri to retrieve the glstring,
    and returns the glstring, source, and resource in a tuple
    """
    uri_fields = list(filter(None, source_uri.split('/')))
    source = uri_fields[-3]
    resource = uri_fields[-2]
    response = requests.get(source_uri)
    if response.status_code == 200:
        glstring = response.text
        return (glstring, source, resource)
    else:
        print("status_code = {}".format(response.status_code))
        print("text = {}".format(response.text))
        sys.exit()


def build_output(s_response, t_response):
    """
    creates the dictionary which will be the output for the program
    """
    output = {
        'sourceGl': s_response['text'],
        'sourceUri': s_response['location'],
        'targetGl': t_response['text'],
        'targetUri': t_response['location'],
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
    group.add_argument("-f", "--jsonfile",
                       help="input file containing JSON",
                       type=str)
    parser.add_argument("-s", "--source",
                        help="Source IMGT/HLA version, e.g., '3.0.0'",
                        type=str)
    parser.add_argument("-t", "--target",
                        help="Target IMGT/HLA version, e.g. '3.25.0'",
                        type=str)
    args = parser.parse_args()

    args = parser.parse_args()
    if (args.glstring is None) and (args.uri is None) and (args.jsonfile is None):
        parser.error("at least one of -g/--glstring or -u/--uri required or -f/--jsonfile")
    if (args.uri) and (args.target is None):
        parser.error("If you specify URI, you need also need to specify "
                     "a -t/--target")
    if (args.glstring) and ((args.target is None) or (args.source is None)):
        parser.error("If you specify GLSTRING, you need to also specify "
                     "both -s/--source and -t/--target")
    if (args.uri) and (args.source):
        print("Warning: source will be obtained from the URI; your specified "
              "-s/--source will be ignored")

    source_uri = args.uri
    glstring = args.glstring
    jsonfile = args.jsonfile
    source = args.source
    target = args.target

    # handle input options
    if jsonfile:
        # same json format used by gl.nmdp.org/imgt-hla/liftover
        with open(jsonfile, 'r') as jf:
            data = json.load(jf)
        target = list(filter(None, data['targetNamespace'].split("/")))[-1]
        source_uri = data['sourceUri']
        glstring, source, resource = from_source_uri(source_uri)
    elif glstring:
        # get source and target from command line
        resource = get_resource(glstring)
    elif source_uri:
        # get target from command line
        glstring, source, resource = from_source_uri(source_uri)

    history = read_history()
    # print("glstring =", glstring)
    # print("source =", source)
    # print("target =", target)
    gl_ids = mk_glids(glstring, source, history)
    # print("IDs =", gl_ids, "\n")
    target_gl = mk_target(gl_ids, target, history)
    if not target_gl:
        print("empty target GL String, all alleles dropped")
        sys.exit()
    # print("target GL = {}\n".format(target_gl))
    s_response = post_gl(glstring, source, resource)
    # print("source location = {}\n".format(s_response['location']))
    t_response = post_gl(target_gl, target, resource)
    outputd= {
        'sourceGl': s_response['text'],
        'sourceUri': s_response['location'],
        'targetGl': t_response['text'],
        'targetUri': t_response['location'],
    }
    output = json.dumps(outputd, sort_keys=True, indent=4)
    # output = json.dumps(build_output(s_response, t_response),
    #                    sort_keys=True, indent=4)
    print(output)


if __name__ == "__main__":
    main()
