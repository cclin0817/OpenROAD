# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2019-2025, The OpenROAD Authors

"""Main API for 3D Block parser."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Union

from .bmap_parser import BmapParser
from .dbv_parser import DbvParser
from .dbx_parser import DbxParser
from .objects import BumpMapData, DbvData, DbxData


class ThreeDBloxParser:
    """Main parser class for 3D Block files.

    This class provides a unified interface for parsing .3dbv, .3dbx,
    and .bmap files.
    """

    def __init__(self, logger: logging.Logger | None = None):
        """Initialize the 3D Block parser.

        Args:
            logger: Optional logger instance. If None, creates a default logger.
        """
        self.logger = logger or self._create_default_logger()

    @staticmethod
    def _create_default_logger() -> logging.Logger:
        """Create a default logger with console handler.

        Returns:
            Configured logger instance.
        """
        logger = logging.getLogger('py3dblox')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(levelname)s - %(name)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def parse(self, filename: str | Path) -> Union[DbvData, DbxData, BumpMapData]:
        """Parse a 3D Block file based on its extension.

        Args:
            filename: Path to the file to parse.

        Returns:
            Parsed data object (DbvData, DbxData, or BumpMapData).

        Raises:
            ValueError: If file extension is not recognized.
            ParserError: If parsing fails.
        """
        filepath = Path(filename)
        extension = filepath.suffix.lower()

        if extension == '.3dbv':
            return self.parse_dbv(filepath)
        elif extension == '.3dbx':
            return self.parse_dbx(filepath)
        elif extension == '.bmap':
            return self.parse_bmap(filepath)
        else:
            raise ValueError(
                f"Unknown file extension: {extension}. "
                f"Expected .3dbv, .3dbx, or .bmap"
            )

    def parse_dbv(self, filename: str | Path) -> DbvData:
        """Parse a .3dbv (3D Block View) file.

        Args:
            filename: Path to the .3dbv file.

        Returns:
            DbvData object containing chiplet definitions.

        Raises:
            ParserError: If parsing fails.
        """
        parser = DbvParser(logger=self.logger)
        return parser.parse_file(filename)

    def parse_dbx(self, filename: str | Path) -> DbxData:
        """Parse a .3dbx (3D Block Exchange) file.

        Args:
            filename: Path to the .3dbx file.

        Returns:
            DbxData object containing design assembly information.

        Raises:
            ParserError: If parsing fails.
        """
        parser = DbxParser(logger=self.logger)
        return parser.parse_file(filename)

    def parse_bmap(self, filename: str | Path) -> BumpMapData:
        """Parse a .bmap (Bump Map) file.

        Args:
            filename: Path to the .bmap file.

        Returns:
            BumpMapData object containing bump map entries.

        Raises:
            ValueError: If parsing fails.
        """
        parser = BmapParser(logger=self.logger)
        return parser.parse_file(filename)


# Convenience functions for direct parsing
def parse_dbv(filename: str | Path, logger: logging.Logger | None = None) -> DbvData:
    """Parse a .3dbv file.

    Args:
        filename: Path to the .3dbv file.
        logger: Optional logger instance.

    Returns:
        DbvData object.
    """
    parser = ThreeDBloxParser(logger=logger)
    return parser.parse_dbv(filename)


def parse_dbx(filename: str | Path, logger: logging.Logger | None = None) -> DbxData:
    """Parse a .3dbx file.

    Args:
        filename: Path to the .3dbx file.
        logger: Optional logger instance.

    Returns:
        DbxData object.
    """
    parser = ThreeDBloxParser(logger=logger)
    return parser.parse_dbx(filename)


def parse_bmap(filename: str | Path, logger: logging.Logger | None = None) -> BumpMapData:
    """Parse a .bmap file.

    Args:
        filename: Path to the .bmap file.
        logger: Optional logger instance.

    Returns:
        BumpMapData object.
    """
    parser = ThreeDBloxParser(logger=logger)
    return parser.parse_bmap(filename)


def parse(filename: str | Path, logger: logging.Logger | None = None) -> Union[DbvData, DbxData, BumpMapData]:
    """Parse a 3D Block file (auto-detect format from extension).

    Args:
        filename: Path to the file.
        logger: Optional logger instance.

    Returns:
        Parsed data object.
    """
    parser = ThreeDBloxParser(logger=logger)
    return parser.parse(filename)
