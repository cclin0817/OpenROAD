# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2019-2025, The OpenROAD Authors

"""Parser for .bmap (Bump Map) files."""

from __future__ import annotations

import logging
from pathlib import Path

from .objects import BumpMapData, BumpMapEntry


class BmapParser:
    """Parser for .bmap files containing bump map information."""

    def __init__(self, logger: logging.Logger | None = None):
        """Initialize the BMAP parser.

        Args:
            logger: Optional logger instance.
        """
        self.logger = logger or logging.getLogger(__name__)
        self.current_file_path: Path | None = None

    def parse_file(self, filename: str | Path) -> BumpMapData:
        """Parse a .bmap file.

        Args:
            filename: Path to the .bmap file.

        Returns:
            BumpMapData object containing parsed entries.

        Raises:
            IOError: If file cannot be opened.
            ValueError: If file format is invalid.
        """
        self.current_file_path = Path(filename)

        try:
            with open(self.current_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except IOError as e:
            error_msg = f"Bump Map Parser Error: Cannot open file: {filename}"
            self.logger.error(error_msg)
            raise IOError(error_msg) from e

        return self._parse_content(content)

    def _parse_content(self, content: str) -> BumpMapData:
        """Parse bump map content.

        Args:
            content: File content string.

        Returns:
            BumpMapData object.

        Raises:
            ValueError: If line format is invalid.
        """
        data = BumpMapData()

        for line_number, line in enumerate(content.splitlines(), start=1):
            # Strip whitespace
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Parse the line
            try:
                entry = self._parse_line(line, line_number)
                data.entries.append(entry)
            except ValueError as e:
                error_msg = (
                    f"Bump Map Parser Error: file {self.current_file_path} "
                    f"Line {line_number} - {e}"
                )
                self.logger.error(error_msg)
                raise ValueError(error_msg) from e

        return data

    def _parse_line(self, line: str, line_number: int) -> BumpMapEntry:
        """Parse a single line from bump map file.

        Args:
            line: Line to parse.
            line_number: Line number (for error messages).

        Returns:
            BumpMapEntry object.

        Raises:
            ValueError: If line format is invalid.
        """
        # Split by whitespace
        tokens = line.split()

        # Expected format: bumpInstName bumpCellType x y portName netName
        if len(tokens) != 6:
            raise ValueError(
                f"Line has {len(tokens)} columns, expected 6. "
                f"Format: bumpInstName bumpCellType x y portName netName"
            )

        bump_inst_name = tokens[0]
        bump_cell_type = tokens[1]

        # Parse coordinates
        try:
            x = float(tokens[2])
            y = float(tokens[3])
        except ValueError as e:
            raise ValueError(f"Invalid coordinate format: {e}") from e

        port_name = tokens[4]
        net_name = tokens[5]

        return BumpMapEntry(
            bump_inst_name=bump_inst_name,
            bump_cell_type=bump_cell_type,
            x=x,
            y=y,
            port_name=port_name,
            net_name=net_name,
        )
