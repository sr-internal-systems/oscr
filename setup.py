# -*- coding: utf-8 -*-
from setuptools import setup

packages = ["oscr"]

package_data = {"": ["*"]}

install_requires = ["requests>=2.22,<3.0", "simple-salesforce>=0.74.3,<0.75.0"]

with open("README.md", "r") as f:
    long_description = f.read()

setup_kwargs = {
    "name": "oscr",
    "version": "0.1.0",
    "description": "The Opinionated System for Contact Retrieval.",
    "long_description": long_description,
    "author": "Elliott Maguire",
    "author_email": "e.maguire@smartrecruiters.com",
    "url": "https://github.com/elliott-maguire/oscr",
    "packages": packages,
    "package_data": package_data,
    "install_requires": install_requires,
    "python_requires": ">=3.6,<4.0",
}


setup(**setup_kwargs)