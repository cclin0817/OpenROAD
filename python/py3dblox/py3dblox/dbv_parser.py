# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2019-2025, The OpenROAD Authors

"""Parser for .3dbv (3D Block View) files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from .base_parser import BaseParser, ParserError
from .objects import (
    ChipletDef,
    ChipletExternal,
    ChipletRegion,
    Coordinate,
    DbvData,
)


class DbvParser(BaseParser):
    """Parser for .3dbv files containing chiplet definitions."""

    def __init__(self, logger: logging.Logger | None = None):
        """Initialize the DBV parser.

        Args:
            logger: Optional logger instance.
        """
        super().__init__(logger)

    def parse_file(self, filename: str | Path) -> DbvData:
        """Parse a .3dbv file.

        Args:
            filename: Path to the .3dbv file.

        Returns:
            DbvData object containing parsed data.

        Raises:
            ParserError: If file cannot be opened or parsed.
        """
        self.current_file_path = Path(filename)

        try:
            with open(self.current_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except IOError as e:
            self.log_error(f"Cannot open file: {filename} - {e}")

        # Parse defines and resolve macros
        content = self.parse_defines(content)

        # Parse YAML content
        return self._parse_yaml_content(content)

    def _parse_yaml_content(self, content: str) -> DbvData:
        """Parse YAML content from .3dbv file.

        Args:
            content: YAML content string.

        Returns:
            DbvData object.

        Raises:
            ParserError: If YAML parsing fails.
        """
        try:
            root = yaml.safe_load(content)
            if root is None:
                root = {}

            data = DbvData()

            if 'Header' in root:
                data.header = self.parse_header(root['Header'])

            if 'ChipletDef' in root:
                data.chiplet_defs = self._parse_chiplet_defs(root['ChipletDef'])

            return data

        except yaml.YAMLError as e:
            self.log_error(f"3DBV YAML parsing error: {e}")

    def _parse_chiplet_defs(self, chiplets_node: dict[str, Any]) -> dict[str, ChipletDef]:
        """Parse ChipletDef section.

        Args:
            chiplets_node: YAML node containing chiplet definitions.

        Returns:
            Dictionary mapping chiplet names to ChipletDef objects.
        """
        chiplet_defs = {}

        for name, chiplet_node in chiplets_node.items():
            chiplet = ChipletDef(name=name)
            self._parse_chiplet(chiplet, chiplet_node)
            chiplet_defs[name] = chiplet

        return chiplet_defs

    def _parse_chiplet(self, chiplet: ChipletDef, chiplet_node: dict[str, Any]) -> None:
        """Parse individual chiplet definition.

        Args:
            chiplet: ChipletDef object to populate.
            chiplet_node: YAML node for this chiplet.

        Raises:
            ParserError: If required fields are missing.
        """
        # Type is required
        if 'type' not in chiplet_node:
            self.log_error(f"Chiplet type is required for chiplet {chiplet.name}")

        chiplet.type = str(chiplet_node['type'])

        # Parse design_area [width, height]
        if 'design_area' in chiplet_node:
            design_area = chiplet_node['design_area']
            if isinstance(design_area, list) and len(design_area) == 2:
                chiplet.design_width = float(design_area[0])
                chiplet.design_height = float(design_area[1])
            else:
                self.log_error(f"design_area must have 2 values for chiplet {chiplet.name}")

        # Parse offset
        if 'offset' in chiplet_node:
            chiplet.offset = self.parse_coordinate(chiplet_node['offset'])

        # Parse seal_ring_width [left, bottom, right, top]
        if 'seal_ring_width' in chiplet_node:
            seal_ring = chiplet_node['seal_ring_width']
            if isinstance(seal_ring, list) and len(seal_ring) == 4:
                chiplet.seal_ring_left = float(seal_ring[0])
                chiplet.seal_ring_bottom = float(seal_ring[1])
                chiplet.seal_ring_right = float(seal_ring[2])
                chiplet.seal_ring_top = float(seal_ring[3])
            else:
                self.log_error(f"seal_ring_width must have 4 values for chiplet {chiplet.name}")

        # Parse scribe_line_remaining_width [left, bottom, right, top]
        if 'scribe_line_remaining_width' in chiplet_node:
            scribe_line = chiplet_node['scribe_line_remaining_width']
            if isinstance(scribe_line, list) and len(scribe_line) == 4:
                chiplet.scribe_line_left = float(scribe_line[0])
                chiplet.scribe_line_bottom = float(scribe_line[1])
                chiplet.scribe_line_right = float(scribe_line[2])
                chiplet.scribe_line_top = float(scribe_line[3])
            else:
                self.log_error(
                    f"scribe_line_remaining_width must have 4 values for chiplet {chiplet.name}"
                )

        # Parse scalar values
        if 'thickness' in chiplet_node:
            chiplet.thickness = float(chiplet_node['thickness'])

        if 'shrink' in chiplet_node:
            chiplet.shrink = float(chiplet_node['shrink'])

        if 'tsv' in chiplet_node:
            chiplet.tsv = bool(chiplet_node['tsv'])

        # Parse regions
        if 'regions' in chiplet_node:
            chiplet.regions = self._parse_regions(chiplet_node['regions'])

        # Parse external references
        if 'external' in chiplet_node:
            chiplet.external = self._parse_external(chiplet_node['external'], chiplet.name)

    def _parse_regions(self, regions_node: dict[str, Any]) -> dict[str, ChipletRegion]:
        """Parse regions section.

        Args:
            regions_node: YAML node containing regions.

        Returns:
            Dictionary mapping region names to ChipletRegion objects.
        """
        regions = {}

        for name, region_node in regions_node.items():
            region = ChipletRegion(name=name)
            self._parse_region(region, region_node)
            regions[name] = region

        return regions

    def _parse_region(self, region: ChipletRegion, region_node: dict[str, Any]) -> None:
        """Parse individual region.

        Args:
            region: ChipletRegion object to populate.
            region_node: YAML node for this region.
        """
        if 'bmap' in region_node:
            region.bmap = str(self.resolve_path(region_node['bmap']))

        if 'pmap' in region_node:
            region.pmap = str(self.resolve_path(region_node['pmap']))

        if 'side' in region_node:
            region.side = str(region_node['side'])

        if 'layer' in region_node:
            region.layer = str(region_node['layer'])

        if 'gds_layer' in region_node:
            region.gds_layer = str(region_node['gds_layer'])

        if 'coords' in region_node:
            region.coords = self.parse_coordinates(region_node['coords'])

    def _parse_external(self, external_node: dict[str, Any], chiplet_name: str) -> ChipletExternal:
        """Parse external file references.

        Args:
            external_node: YAML node containing external references.
            chiplet_name: Name of the chiplet (for error messages).

        Returns:
            ChipletExternal object.
        """
        external = ChipletExternal()

        # Parse LEF files
        if 'LEF_file' in external_node:
            lef_files = external_node['LEF_file']
            if isinstance(lef_files, list):
                for lef_file in lef_files:
                    external.lef_files.extend(self.resolve_paths(str(lef_file)))
            else:
                external.lef_files.extend(self.resolve_paths(str(lef_files)))

        # Parse APR tech files
        if 'APR_tech_file' in external_node:
            tech_files = external_node['APR_tech_file']
            if isinstance(tech_files, list):
                for tech_file in tech_files:
                    external.tech_lef_files.extend(self.resolve_paths(str(tech_file)))
            else:
                external.tech_lef_files.extend(self.resolve_paths(str(tech_files)))

        # Parse liberty files
        if 'liberty_file' in external_node:
            lib_files = external_node['liberty_file']
            if isinstance(lib_files, list):
                for lib_file in lib_files:
                    external.lib_files.extend(self.resolve_paths(str(lib_file)))
            else:
                external.lib_files.extend(self.resolve_paths(str(lib_files)))

        # Parse DEF file
        if 'DEF_file' in external_node:
            external.def_file = str(self.resolve_path(external_node['DEF_file']))

        return external
