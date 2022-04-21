#!/usr/bin/env python

import os
from setuptools import setup
from pathlib import Path
import sys

_dir = Path(__file__).resolve().parent


with open(f"{_dir}/README.md") as f:
    long_desc = """

    ## Docs

    """
    try:
        long_desc += f.read()
    except UnicodeDecodeError:
        long_desc += ""


if sys.version_info > (3, 7, 0):
    install_requires = ['authlib', 'requests',
                        'click', 'tabulate', 'pandas', 'numpy']
else:
    print(sys.version_info)
    install_requires = ['authlib', 'requests', 'click']
    print(install_requires)

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
    version='0.1.1',
    scripts=['python/SuperfacilityAPI/bin/sfapi'],
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
    ],
    python_requires=">=3.5",
)
