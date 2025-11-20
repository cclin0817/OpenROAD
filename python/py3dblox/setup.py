# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2019-2025, The OpenROAD Authors

"""Setup script for py3dblox package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text(encoding="utf-8")

setup(
    name="py3dblox",
    version="1.0.0",
    author="The OpenROAD Authors",
    author_email="openroad@ucsd.edu",
    description="Python parser for 3D Block files (.3dbv, .3dbx, .bmap)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/The-OpenROAD-Project/OpenROAD",
    project_urls={
        "Bug Tracker": "https://github.com/The-OpenROAD-Project/OpenROAD/issues",
        "Documentation": "https://openroad.readthedocs.io/",
        "Source Code": "https://github.com/The-OpenROAD-Project/OpenROAD",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.10",
    install_requires=[
        "PyYAML>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "ruff>=0.1.0",
        ],
        "viewer": [
            "matplotlib>=3.5.0",
            "numpy>=1.20.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "py3dblox=py3dblox.__main__:main",
            "py3dblox-viewer=py3dblox.viewer:main",
        ],
    },
    keywords="eda, 3d-ic, chiplet, parser, yaml",
    license="BSD-3-Clause",
    zip_safe=False,
)
