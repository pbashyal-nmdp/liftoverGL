#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('COPYING.LESSER') as f:
    license = f.read()

setup(
    name='pyliftover',
    version='0.1.0',
    description='convers a GL String from one version of the IMGT/HLA nomenclature to another',
    long_description=readme,
    author='Bob Milius',
    author_email='bmilius@nmdp.org',
    url='https://github.com/nmdp-bioinformatics/pyliftover',
    license=license,
    packages=find_packages(exclude=('tests', 'docs', 'bin'))
)

