# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2019-2025, The OpenROAD Authors

"""Base parser class with common YAML parsing utilities."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import yaml

from .objects import Coordinate, Header


class ParserError(Exception):
    """Exception raised for parser errors."""
    pass


class BaseParser:
    """Base parser with common functionality for YAML-based parsers."""

    def __init__(self, logger: logging.Logger | None = None):
        """Initialize the base parser.

        Args:
            logger: Optional logger instance. If None, creates a default logger.
        """
        self.logger = logger or logging.getLogger(__name__)
        self.current_file_path: Path | None = None
        self._defines: dict[str, str] = {}

    def parse_defines(self, content: str) -> str:
        """Parse and resolve #!define statements in content.

        Args:
            content: File content with potential define statements.

        Returns:
            Content with defines resolved.
        """
        self._defines.clear()
        processed_lines = []

        for line in content.splitlines():
            if line.startswith("#!define"):
                # Extract define statement
                define_stmt = line[8:].strip()
                parts = define_stmt.split(maxsplit=1)
                if len(parts) == 2:
                    key, value = parts
                    self._defines[key.strip()] = value.strip()
                # Don't include define statements in output
                continue

            # Resolve any macros in the line
            resolved_line = line
            for macro, replacement in self._defines.items():
                resolved_line = resolved_line.replace(macro, replacement)

            processed_lines.append(resolved_line)

        return '\n'.join(processed_lines)

    def resolve_path(self, path: str) -> Path:
        """Resolve a path relative to the current file.

        Args:
            path: Path to resolve (can be absolute or relative).

        Returns:
            Resolved absolute path.
        """
        path_obj = Path(path)
        if path_obj.is_absolute():
            return path_obj

        if self.current_file_path is None:
            return path_obj.absolute()

        current_dir = self.current_file_path.parent
        return (current_dir / path_obj).resolve()

    def resolve_paths(self, path_pattern: str) -> list[str]:
        """Resolve paths, supporting wildcards.

        Args:
            path_pattern: Path pattern (may contain * wildcard).

        Returns:
            List of resolved path strings.
        """
        resolved = self.resolve_path(path_pattern)

        if '*' in path_pattern:
            # Handle glob patterns
            directory = resolved.parent
            pattern = resolved.name

            if not directory.exists() or not directory.is_dir():
                self.log_error(f"Directory does not exist: {directory}")
                return []

            matching_files = []
            for file_path in directory.iterdir():
                if file_path.is_file() and self._matches_pattern(file_path.name, pattern):
                    matching_files.append(str(file_path))

            return matching_files
        else:
            return [str(resolved)]

    @staticmethod
    def _matches_pattern(filename: str, pattern: str) -> bool:
        """Check if filename matches a simple glob pattern.

        Args:
            filename: Filename to check.
            pattern: Pattern with * wildcard.

        Returns:
            True if filename matches pattern.
        """
        if '*' not in pattern:
            return filename == pattern

        star_pos = pattern.find('*')
        prefix = pattern[:star_pos]
        suffix = pattern[star_pos + 1:]

        if len(filename) < len(prefix) + len(suffix):
            return False

        return filename.startswith(prefix) and filename.endswith(suffix)

    def parse_coordinate(self, coord_node: Any) -> Coordinate:
        """Parse a coordinate from YAML node.

        Args:
            coord_node: YAML node representing [x, y] coordinate.

        Returns:
            Coordinate object.

        Raises:
            ParserError: If coordinate format is invalid.
        """
        if not isinstance(coord_node, list) or len(coord_node) != 2:
            self.log_error("Coordinate must be an array [x, y]")

        try:
            return Coordinate(x=float(coord_node[0]), y=float(coord_node[1]))
        except (ValueError, TypeError) as e:
            self.log_error(f"Error parsing coordinate: {e}")

    def parse_coordinates(self, coords_node: Any) -> list[Coordinate]:
        """Parse a list of coordinates from YAML node.

        Args:
            coords_node: YAML node representing list of coordinates.

        Returns:
            List of Coordinate objects.
        """
        if not isinstance(coords_node, list):
            return []

        return [self.parse_coordinate(coord) for coord in coords_node]

    def parse_header(self, header_node: dict[str, Any]) -> Header:
        """Parse header section from YAML.

        Args:
            header_node: YAML node containing header information.

        Returns:
            Header object.
        """
        header = Header()

        if 'version' in header_node:
            version = self.extract_value(header_node, 'version', str)
            header.version = version if version is not None else ""

        if 'unit' in header_node:
            unit = self.extract_value(header_node, 'unit', str)
            header.unit = unit if unit is not None else ""

        if 'precision' in header_node:
            header.precision = int(header_node['precision'])

        if 'include' in header_node:
            includes = header_node['include']
            if isinstance(includes, list):
                for include in includes:
                    include_str = str(include) if include is not None else ""
                    if include_str:
                        header.includes.extend(self.resolve_paths(include_str))

        return header

    def extract_value(self, node: dict[str, Any], key: str, value_type: type = str) -> Any:
        """Extract and convert a value from YAML node.

        Args:
            node: YAML dictionary node.
            key: Key to extract.
            value_type: Expected type to convert to.

        Returns:
            Extracted value of specified type, or None if the value is null.

        Raises:
            ParserError: If value extraction or conversion fails.
        """
        if key not in node:
            return None

        try:
            value = node[key]
            # Preserve None values instead of converting to string "None"
            if value is None:
                return None
            if value_type == list:
                return list(value) if isinstance(value, (list, tuple)) else [value]
            return value_type(value)
        except (ValueError, TypeError) as e:
            self.log_error(f"Error parsing value for '{key}': {e}")

    def log_error(self, message: str) -> None:
        """Log an error and raise ParserError.

        Args:
            message: Error message.

        Raises:
            ParserError: Always raised with the given message.
        """
        full_message = f"Parser Error: {message}"
        self.logger.error(full_message)
        raise ParserError(full_message)

    @staticmethod
    def trim(text: str) -> str:
        """Trim whitespace from string.

        Args:
            text: String to trim.

        Returns:
            Trimmed string.
        """
        return text.strip()
