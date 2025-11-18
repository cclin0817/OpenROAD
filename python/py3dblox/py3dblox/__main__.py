# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2019-2025, The OpenROAD Authors

"""Command-line interface for py3dblox parser."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path

from .parser import ThreeDBloxParser, parse


def setup_logging(verbose: bool) -> logging.Logger:
    """Set up logging configuration.

    Args:
        verbose: Enable verbose (DEBUG) logging.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger('py3dblox')
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG if verbose else logging.INFO)

    formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def format_output(data, output_format: str) -> str:
    """Format parsed data for output.

    Args:
        data: Parsed data object (DbvData, DbxData, or BumpMapData).
        output_format: Output format ('json' or 'pretty').

    Returns:
        Formatted string.
    """
    data_dict = asdict(data)

    if output_format == 'json':
        return json.dumps(data_dict, indent=2)
    elif output_format == 'pretty':
        return format_pretty(data_dict)
    else:
        return str(data_dict)


def format_pretty(data: dict, indent: int = 0) -> str:
    """Format data in a human-readable format.

    Args:
        data: Data dictionary.
        indent: Current indentation level.

    Returns:
        Pretty-formatted string.
    """
    lines = []
    indent_str = "  " * indent

    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{indent_str}{key}:")
            lines.append(format_pretty(value, indent + 1))
        elif isinstance(value, list):
            if not value:
                lines.append(f"{indent_str}{key}: []")
            elif isinstance(value[0], dict):
                lines.append(f"{indent_str}{key}:")
                for item in value:
                    lines.append(format_pretty(item, indent + 1))
                    lines.append("")
            else:
                lines.append(f"{indent_str}{key}: {value}")
        else:
            lines.append(f"{indent_str}{key}: {value}")

    return "\n".join(lines)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Parse 3D Block files (.3dbv, .3dbx, .bmap)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse a .3dbv file and output as JSON
  python -m py3dblox parse example.3dbv --format json

  # Parse a .3dbx file with verbose logging
  python -m py3dblox parse example.3dbx -v

  # Parse and save output to file
  python -m py3dblox parse example.bmap -o output.json

  # Validate a file without output
  python -m py3dblox validate example.3dbv
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Parse command
    parse_parser = subparsers.add_parser('parse', help='Parse a 3D Block file')
    parse_parser.add_argument('file', type=str, help='File to parse')
    parse_parser.add_argument(
        '-f', '--format',
        choices=['json', 'pretty', 'dict'],
        default='pretty',
        help='Output format (default: pretty)'
    )
    parse_parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output file (default: stdout)'
    )
    parse_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate a 3D Block file')
    validate_parser.add_argument('file', type=str, help='File to validate')
    validate_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    # Info command
    info_parser = subparsers.add_parser('info', help='Show file information')
    info_parser.add_argument('file', type=str, help='File to inspect')
    info_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    logger = setup_logging(args.verbose if hasattr(args, 'verbose') else False)

    try:
        if args.command == 'parse':
            # Parse the file
            data = parse(args.file, logger=logger)

            # Format output
            output = format_output(data, args.format)

            # Write to file or stdout
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(output)
                logger.info(f"Output written to {args.output}")
            else:
                print(output)

        elif args.command == 'validate':
            # Just try to parse - if it succeeds, file is valid
            parse(args.file, logger=logger)
            print(f"✓ {args.file} is valid")

        elif args.command == 'info':
            # Show file information
            filepath = Path(args.file)
            data = parse(args.file, logger=logger)

            print(f"File: {filepath.name}")
            print(f"Type: {filepath.suffix}")
            print(f"Size: {filepath.stat().st_size} bytes")
            print()

            # Type-specific info
            from .objects import DbvData, DbxData, BumpMapData

            if isinstance(data, DbvData):
                print("Format: 3D Block View (.3dbv)")
                print(f"Chiplets defined: {len(data.chiplet_defs)}")
                for name, chiplet in data.chiplet_defs.items():
                    print(f"  - {name} ({chiplet.type})")
                    print(f"    Regions: {len(chiplet.regions)}")

            elif isinstance(data, DbxData):
                print("Format: 3D Block Exchange (.3dbx)")
                print(f"Design: {data.design.name}")
                print(f"Chiplet instances: {len(data.chiplet_instances)}")
                for name, inst in data.chiplet_instances.items():
                    print(f"  - {name} (ref: {inst.reference})")
                print(f"Connections: {len(data.connections)}")

            elif isinstance(data, BumpMapData):
                print("Format: Bump Map (.bmap)")
                print(f"Bump entries: {len(data.entries)}")

    except Exception as e:
        logger.error(f"Error: {e}")
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
