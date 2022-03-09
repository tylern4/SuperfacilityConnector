#!/usr/bin/env python

import os
from setuptools import setup
from pathlib import Path
import sys

_dir = Path(__file__).resolve().parent

with open(f"{_dir}/README.md") as f:
    long_desc = f.read()

print(sys.version_info)
if sys.version_info > (3,7,0):
    install_requires=['authlib', 'requests', 'click', 'tabulate', 'pandas', 'numpy']
else:
    install_requires=['authlib', 'requests']
    
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
    version='0.0.2',
    scripts=['python/SuperfacilityAPI/bin/sfapi'],
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
    ],
    python_requires=">=3.5",
)
