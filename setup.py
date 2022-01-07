#!/usr/bin/env python

import os
from setuptools import setup
from pathlib import Path

_dir = Path(__file__).resolve().parent

with open(f"{_dir}/README.md") as f:
    long_desc = f.read()


def get_version():
    try:
        ver = os.popen('git describe').read()
        ver = ver.split('-')[0][1:]

        return ver
    except:
        return 'error'


setup(
    name="SuperfacilityConnector",
    description="Connector API NERSC Superfacility",
    long_description=long_desc,
    long_description_content_type="text/markdown",
    url="https://github.com/tylern4/superfacilityConnector",
    author="Nick Tyler",
    author_email="tylern@lbl.gov",
    packages=['SuperfacilityAPI'],
    package_dir={'': 'python'},
    version=get_version(),
    scripts=['python/SuperfacilityAPI/bin/sfapi'],
    install_requires=[
        'authlib', 'requests', 'click', 'tabulate', 'pandas', 'numpy'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
    ],
    python_requires=">=3.7",
)
