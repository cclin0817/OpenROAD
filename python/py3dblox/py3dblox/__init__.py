# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2019-2025, The OpenROAD Authors

"""
py3dblox - Python parser for 3D Block files.

This package provides parsers for:
  - .3dbv (3D Block View) - Chiplet definitions
  - .3dbx (3D Block Exchange) - Design assembly
  - .bmap (Bump Map) - Bump locations

Usage:
    >>> from py3dblox import parse, parse_dbv, parse_dbx, parse_bmap
    >>>
    >>> # Auto-detect file type
    >>> data = parse("design.3dbx")
    >>>
    >>> # Parse specific formats
    >>> dbv_data = parse_dbv("chiplet.3dbv")
    >>> dbx_data = parse_dbx("design.3dbx")
    >>> bmap_data = parse_bmap("bumps.bmap")
"""

__version__ = "1.0.0"
__author__ = "The OpenROAD Authors"
__license__ = "BSD-3-Clause"

# Import main API
from .parser import (
    ThreeDBloxParser,
    parse,
    parse_bmap,
    parse_dbv,
    parse_dbx,
)

# Import individual parsers
from .bmap_parser import BmapParser
from .dbv_parser import DbvParser
from .dbx_parser import DbxParser

# Import data structures
from .objects import (
    BumpMapData,
    BumpMapEntry,
    ChipletDef,
    ChipletExternal,
    ChipletInst,
    ChipletInstExternal,
    ChipletRegion,
    Connection,
    Coordinate,
    DbvData,
    DbxData,
    DesignDef,
    DesignExternal,
    Header,
)

# Import exceptions
from .base_parser import ParserError

__all__ = [
    # Version
    "__version__",
    # Main API
    "ThreeDBloxParser",
    "parse",
    "parse_dbv",
    "parse_dbx",
    "parse_bmap",
    # Individual parsers
    "DbvParser",
    "DbxParser",
    "BmapParser",
    # Data structures
    "DbvData",
    "DbxData",
    "BumpMapData",
    "Header",
    "ChipletDef",
    "ChipletRegion",
    "ChipletExternal",
    "ChipletInst",
    "ChipletInstExternal",
    "DesignDef",
    "DesignExternal",
    "Connection",
    "Coordinate",
    "BumpMapEntry",
    # Exceptions
    "ParserError",
]
