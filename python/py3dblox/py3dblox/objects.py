# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2019-2025, The OpenROAD Authors

"""Data structures for 3D Block parser."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Coordinate:
    """Represents a 2D coordinate."""
    x: float = 0.0
    y: float = 0.0


@dataclass
class ChipletRegion:
    """Represents a chiplet region definition."""
    name: str = ""
    bmap: str = ""
    pmap: str = ""
    side: str = ""
    layer: str = ""
    gds_layer: str = ""
    coords: list[Coordinate] = field(default_factory=list)


@dataclass
class ChipletExternal:
    """External file references for a chiplet."""
    lef_files: list[str] = field(default_factory=list)
    tech_lef_files: list[str] = field(default_factory=list)
    lib_files: list[str] = field(default_factory=list)
    def_file: str = ""


@dataclass
class ChipletDef:
    """Chiplet definition from .3dbv file."""
    name: str = ""
    type: str = ""

    # Design area components
    design_width: float = -1.0
    design_height: float = -1.0
    offset: Coordinate = field(default_factory=Coordinate)

    seal_ring_left: float = -1.0
    seal_ring_bottom: float = -1.0
    seal_ring_right: float = -1.0
    seal_ring_top: float = -1.0

    scribe_line_left: float = -1.0
    scribe_line_bottom: float = -1.0
    scribe_line_right: float = -1.0
    scribe_line_top: float = -1.0

    thickness: float = -1.0
    shrink: float = -1.0
    tsv: bool = False

    regions: dict[str, ChipletRegion] = field(default_factory=dict)
    external: ChipletExternal = field(default_factory=ChipletExternal)


@dataclass
class Header:
    """Header information common to both .3dbv and .3dbx files."""
    version: str = ""
    unit: str = ""
    precision: int = 1
    includes: list[str] = field(default_factory=list)


@dataclass
class DbvData:
    """Complete data from a .3dbv file."""
    header: Header = field(default_factory=Header)
    chiplet_defs: dict[str, ChipletDef] = field(default_factory=dict)


@dataclass
class DesignExternal:
    """External file references for a design."""
    verilog_file: str = ""


@dataclass
class DesignDef:
    """Design definition from .3dbx file."""
    name: str = ""
    external: DesignExternal = field(default_factory=DesignExternal)


@dataclass
class ChipletInstExternal:
    """External file references for a chiplet instance."""
    verilog_file: str = ""
    sdc_file: str = ""
    def_file: str = ""


@dataclass
class ChipletInst:
    """Chiplet instance definition."""
    name: str = ""
    reference: str = ""
    external: ChipletInstExternal = field(default_factory=ChipletInstExternal)

    # Stack information
    loc: Coordinate = field(default_factory=Coordinate)
    z: float = 0.0
    orient: str = ""


@dataclass
class Connection:
    """Connection between chiplet regions."""
    name: str = ""
    top: str = ""
    bot: str = ""
    thickness: float = 0.0


@dataclass
class DbxData:
    """Complete data from a .3dbx file."""
    header: Header = field(default_factory=Header)
    design: DesignDef = field(default_factory=DesignDef)
    chiplet_instances: dict[str, ChipletInst] = field(default_factory=dict)
    connections: dict[str, Connection] = field(default_factory=dict)


@dataclass
class BumpMapEntry:
    """Single entry in a bump map file."""
    bump_inst_name: str
    bump_cell_type: str
    x: float
    y: float
    port_name: str
    net_name: str


@dataclass
class BumpMapData:
    """Complete data from a .bmap file."""
    entries: list[BumpMapEntry] = field(default_factory=list)
