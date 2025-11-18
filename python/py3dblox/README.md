# py3dblox - Python 3D Block Parser

A Python library for parsing 3D Block files used in 3D-IC design workflows.

## Overview

`py3dblox` is a standalone Python parser for three file formats used in 3D integrated circuit design:

- **`.3dbv`** (3D Block View) - YAML-based chiplet definition files
- **`.3dbx`** (3D Block Exchange) - YAML-based design assembly files
- **`.bmap`** (Bump Map) - Text-based bump location files

This library is based on the C++ parser implementation in [OpenROAD](https://github.com/The-OpenROAD-Project/OpenROAD).

## Features

- Parse all three 3D Block file formats
- Pythonic API with dataclasses for structured data
- Command-line interface for file validation and conversion
- Support for `#!define` macro expansion
- Path resolution for included files
- Comprehensive error reporting with Python logging

## Installation

### From source

```bash
cd python/py3dblox
pip install .
```

### Development installation

```bash
cd python/py3dblox
pip install -e ".[dev]"
```

## Requirements

- Python 3.12 or higher
- PyYAML 6.0 or higher

## Usage

### Python API

#### Basic Usage

```python
from py3dblox import parse, parse_dbv, parse_dbx, parse_bmap

# Auto-detect file type from extension
data = parse("design.3dbx")

# Parse specific formats
dbv_data = parse_dbv("chiplet.3dbv")
dbx_data = parse_dbx("design.3dbx")
bmap_data = parse_bmap("bumps.bmap")
```

#### Working with Parsed Data

```python
from py3dblox import parse_dbv

# Parse a .3dbv file
data = parse_dbv("example.3dbv")

# Access header information
print(f"Version: {data.header.version}")
print(f"Precision: {data.header.precision}")

# Access chiplet definitions
for name, chiplet in data.chiplet_defs.items():
    print(f"Chiplet: {name}")
    print(f"  Type: {chiplet.type}")
    print(f"  Size: {chiplet.design_width} x {chiplet.design_height}")
    print(f"  Thickness: {chiplet.thickness}")

    # Access regions
    for region_name, region in chiplet.regions.items():
        print(f"  Region: {region_name}")
        print(f"    Side: {region.side}")
        print(f"    Coordinates: {len(region.coords)}")
```

#### Working with .3dbx Files

```python
from py3dblox import parse_dbx

data = parse_dbx("design.3dbx")

# Access design information
print(f"Design: {data.design.name}")

# Access chiplet instances
for name, inst in data.chiplet_instances.items():
    print(f"Instance: {name}")
    print(f"  Reference: {inst.reference}")
    print(f"  Location: ({inst.loc.x}, {inst.loc.y}, {inst.z})")
    print(f"  Orientation: {inst.orient}")

# Access connections
for name, conn in data.connections.items():
    print(f"Connection: {name}")
    print(f"  Top: {conn.top}")
    print(f"  Bottom: {conn.bot}")
    print(f"  Thickness: {conn.thickness}")
```

#### Working with .bmap Files

```python
from py3dblox import parse_bmap

data = parse_bmap("bumps.bmap")

# Access bump entries
for entry in data.entries:
    print(f"Bump: {entry.bump_inst_name}")
    print(f"  Type: {entry.bump_cell_type}")
    print(f"  Position: ({entry.x}, {entry.y})")
    print(f"  Port: {entry.port_name}")
    print(f"  Net: {entry.net_name}")
```

#### Custom Logging

```python
import logging
from py3dblox import ThreeDBloxParser

# Configure custom logger
logger = logging.getLogger("my_app")
logger.setLevel(logging.DEBUG)

# Use with parser
parser = ThreeDBloxParser(logger=logger)
data = parser.parse_dbv("chiplet.3dbv")
```

### Command-Line Interface

The package provides a `py3dblox` command-line tool.

#### Parse a file

```bash
# Parse and display in pretty format (default)
py3dblox parse design.3dbx

# Parse and output as JSON
py3dblox parse design.3dbx --format json

# Parse and save to file
py3dblox parse design.3dbx --format json -o output.json

# Enable verbose logging
py3dblox parse chiplet.3dbv -v
```

#### Validate a file

```bash
# Validate file syntax
py3dblox validate design.3dbx
```

#### Show file information

```bash
# Display file metadata and summary
py3dblox info design.3dbx
```

## File Format Examples

### .3dbv Format (Chiplet Definition)

```yaml
#!define NG45_PATH ../Nangate45

Header:
  version: 2.5
  unit: micron
  precision: 2000

ChipletDef:
  SoC:
    type: die
    design_area: [955, 1082]
    shrink: 1
    tsv: false
    thickness: 300
    offset: [0, 0]
    regions:
      r1:
        side: front
        bmap: example.bmap
        layer: UBM
        coords:
          - [0, 0]
          - [955, 0]
          - [955, 1082]
          - [0, 1082]
    external:
      APR_tech_file: [NG45_PATH/*_tech.lef]
      LEF_file: [NG45_PATH/macros.lef]
      DEF_file: ../design.def
```

### .3dbx Format (Design Assembly)

```yaml
Header:
  version: "1.0"
  unit: "micron"
  precision: 2000
  include:
    - chiplets.3dbv

Design:
  name: "TopDesign"
  external:
    verilog_file: "top.v"

ChipletInst:
  cpu_inst:
    reference: CPU
  mem_inst:
    reference: Memory

Stack:
  cpu_inst:
    loc: [0.0, 0.0]
    z: 0.0
    orient: R0
  mem_inst:
    loc: [0.0, 0.0]
    z: 300.0
    orient: MZ

Connection:
  cpu_to_mem:
    top: mem_inst.regions.bottom
    bot: cpu_inst.regions.top
    thickness: 2.0
```

### .bmap Format (Bump Map)

```
# bumpInstName bumpCellType x y portName netName
bump1 BUMP 100.0 200.0 SIG1 SIG1
bump2 BUMP 150.0 200.0 SIG2 SIG2
bump3 BUMP 200.0 200.0 - -
```

## Data Structures

All parsed data is returned as Python dataclasses:

- `DbvData` - Complete .3dbv file data
  - `Header` - File header information
  - `ChipletDef` - Chiplet definitions
  - `ChipletRegion` - Region definitions
  - `ChipletExternal` - External file references

- `DbxData` - Complete .3dbx file data
  - `Header` - File header information
  - `DesignDef` - Design definition
  - `ChipletInst` - Chiplet instances
  - `Connection` - Inter-chiplet connections

- `BumpMapData` - Complete .bmap file data
  - `BumpMapEntry` - Individual bump entries

- `Coordinate` - 2D coordinate (x, y)

All dataclasses can be converted to dictionaries using Python's `dataclasses.asdict()`:

```python
from dataclasses import asdict
import json

data = parse_dbv("chiplet.3dbv")
data_dict = asdict(data)
json_str = json.dumps(data_dict, indent=2)
```

## Error Handling

The parser raises `ParserError` exceptions for parsing errors:

```python
from py3dblox import parse, ParserError

try:
    data = parse("invalid.3dbv")
except ParserError as e:
    print(f"Parse error: {e}")
except FileNotFoundError as e:
    print(f"File not found: {e}")
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black py3dblox/
ruff check py3dblox/
```

## License

BSD-3-Clause

Copyright (c) 2019-2025, The OpenROAD Authors

## Related Projects

- [OpenROAD](https://github.com/The-OpenROAD-Project/OpenROAD) - Foundational RTL-to-GDSII flow
- [OpenROAD-flow-scripts](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts) - RTL-to-GDSII flow scripts

## Contributing

Contributions are welcome! Please submit pull requests to the OpenROAD repository.

## Support

For issues and questions, please use the [OpenROAD GitHub Issues](https://github.com/The-OpenROAD-Project/OpenROAD/issues).
