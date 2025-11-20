# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2019-2025, The OpenROAD Authors

"""Parser for .3dbx (3D Block Exchange) files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from .base_parser import BaseParser, ParserError
from .objects import (
    ChipletInst,
    ChipletInstExternal,
    Connection,
    DbxData,
    DesignDef,
    DesignExternal,
)


class DbxParser(BaseParser):
    """Parser for .3dbx files containing design assembly information."""

    def __init__(self, logger: logging.Logger | None = None):
        """Initialize the DBX parser.

        Args:
            logger: Optional logger instance.
        """
        super().__init__(logger)

    def parse_file(self, filename: str | Path) -> DbxData:
        """Parse a .3dbx file.

        Args:
            filename: Path to the .3dbx file.

        Returns:
            DbxData object containing parsed data.

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

    def _parse_yaml_content(self, content: str) -> DbxData:
        """Parse YAML content from .3dbx file.

        Args:
            content: YAML content string.

        Returns:
            DbxData object.

        Raises:
            ParserError: If YAML parsing fails.
        """
        try:
            root = yaml.safe_load(content)
            if root is None:
                root = {}

            data = DbxData()

            if 'Header' in root:
                data.header = self.parse_header(root['Header'])

            if 'Design' in root:
                data.design = self._parse_design(root['Design'])

            if 'ChipletInst' in root:
                data.chiplet_instances = self._parse_chiplet_insts(root['ChipletInst'])

            if 'Stack' in root:
                self._parse_stack(data.chiplet_instances, root['Stack'])

            if 'Connection' in root:
                data.connections = self._parse_connections(root['Connection'])

            return data

        except yaml.YAMLError as e:
            self.log_error(f"DBX YAML parsing error: {e}")

    def _parse_design(self, design_node: dict[str, Any]) -> DesignDef:
        """Parse Design section.

        Args:
            design_node: YAML node containing design information.

        Returns:
            DesignDef object.

        Raises:
            ParserError: If design name is missing.
        """
        if 'name' not in design_node:
            self.log_error("DBX Design name is required")

        name = self.extract_value(design_node, 'name', str)
        design = DesignDef(name=name if name is not None else "")

        if 'external' in design_node:
            design.external = self._parse_design_external(design_node['external'])

        return design

    def _parse_design_external(self, external_node: dict[str, Any]) -> DesignExternal:
        """Parse design external file references.

        Args:
            external_node: YAML node containing external references.

        Returns:
            DesignExternal object.
        """
        external = DesignExternal()

        if 'verilog_file' in external_node:
            verilog_file = self.extract_value(external_node, 'verilog_file', str)
            if verilog_file is not None:
                external.verilog_file = str(self.resolve_path(verilog_file))

        return external

    def _parse_chiplet_insts(self, instances_node: dict[str, Any]) -> dict[str, ChipletInst]:
        """Parse ChipletInst section.

        Args:
            instances_node: YAML node containing chiplet instances.

        Returns:
            Dictionary mapping instance names to ChipletInst objects.
        """
        instances = {}

        for name, instance_node in instances_node.items():
            instance = ChipletInst(name=name)
            self._parse_chiplet_inst(instance, instance_node)
            instances[name] = instance

        return instances

    def _parse_chiplet_inst(self, instance: ChipletInst, instance_node: dict[str, Any]) -> None:
        """Parse individual chiplet instance.

        Args:
            instance: ChipletInst object to populate.
            instance_node: YAML node for this instance.

        Raises:
            ParserError: If reference is missing.
        """
        if 'reference' not in instance_node:
            self.log_error(f"DBX ChipletInst reference is required for instance {instance.name}")

        reference = self.extract_value(instance_node, 'reference', str)
        instance.reference = reference if reference is not None else ""

        if 'external' in instance_node:
            instance.external = self._parse_chiplet_inst_external(instance_node['external'])

    def _parse_chiplet_inst_external(self, external_node: dict[str, Any]) -> ChipletInstExternal:
        """Parse chiplet instance external file references.

        Args:
            external_node: YAML node containing external references.

        Returns:
            ChipletInstExternal object.
        """
        external = ChipletInstExternal()

        if 'verilog_file' in external_node:
            verilog_file = self.extract_value(external_node, 'verilog_file', str)
            if verilog_file is not None:
                external.verilog_file = str(self.resolve_path(verilog_file))

        if 'sdc_file' in external_node:
            sdc_file = self.extract_value(external_node, 'sdc_file', str)
            if sdc_file is not None:
                external.sdc_file = str(self.resolve_path(sdc_file))

        if 'def_file' in external_node:
            def_file = self.extract_value(external_node, 'def_file', str)
            if def_file is not None:
                external.def_file = str(self.resolve_path(def_file))

        return external

    def _parse_stack(
        self, instances: dict[str, ChipletInst], stack_node: dict[str, Any]
    ) -> None:
        """Parse Stack section and update chiplet instances.

        Args:
            instances: Dictionary of chiplet instances to update.
            stack_node: YAML node containing stack information.

        Raises:
            ParserError: If stack instance not found in ChipletInst.
        """
        for instance_name, stack_instance_node in stack_node.items():
            if instance_name not in instances:
                self.log_error(
                    f"DBX Stack instance '{instance_name}' not found in ChipletInst"
                )

            instance = instances[instance_name]
            self._parse_stack_instance(instance, stack_instance_node)

    def _parse_stack_instance(
        self, instance: ChipletInst, stack_instance_node: dict[str, Any]
    ) -> None:
        """Parse stack information for a chiplet instance.

        Args:
            instance: ChipletInst object to update.
            stack_instance_node: YAML node containing stack info.

        Raises:
            ParserError: If required stack fields are missing.
        """
        if 'loc' not in stack_instance_node:
            self.log_error(f"DBX Stack location is required for instance {instance.name}")

        instance.loc = self.parse_coordinate(stack_instance_node['loc'])

        if 'z' not in stack_instance_node:
            self.log_error(f"DBX Stack z is required for instance {instance.name}")

        instance.z = float(stack_instance_node['z'])

        if 'orient' not in stack_instance_node:
            self.log_error(f"DBX Stack orientation is required for instance {instance.name}")

        orient = self.extract_value(stack_instance_node, 'orient', str)
        instance.orient = orient if orient is not None else ""

    def _parse_connections(self, connections_node: dict[str, Any]) -> dict[str, Connection]:
        """Parse Connection section.

        Args:
            connections_node: YAML node containing connections.

        Returns:
            Dictionary mapping connection names to Connection objects.
        """
        connections = {}

        for name, connection_node in connections_node.items():
            connection = Connection(name=name)
            self._parse_connection(connection, connection_node)
            connections[name] = connection

        return connections

    def _parse_connection(self, connection: Connection, connection_node: dict[str, Any]) -> None:
        """Parse individual connection.

        Args:
            connection: Connection object to populate.
            connection_node: YAML node for this connection.

        Raises:
            ParserError: If required connection fields are missing.
        """
        if 'top' not in connection_node:
            self.log_error(f"DBX Connection top is required for connection {connection.name}")

        connection.top = self.extract_value(connection_node, 'top', str)

        # Parse bot region (required, can be null/~)
        if 'bot' not in connection_node:
            self.log_error(f"DBX Connection bot is required for connection {connection.name}")

        connection.bot = self.extract_value(connection_node, 'bot', str)

        if 'thickness' in connection_node:
            connection.thickness = float(connection_node['thickness'])
