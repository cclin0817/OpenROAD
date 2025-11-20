# 3D Blox GUI Viewer - Quick Start Guide

A graphical user interface for visualizing 3D chiplet stacking structures from `.3dbx` and `.3dbv` files.

## Installation

Install py3dblox with viewer support:

```bash
cd python/py3dblox
pip install -e ".[viewer]"
```

This installs the required dependencies: matplotlib and numpy.

## Quick Start

### Launch the Viewer

**Option 1: Command-line tool**
```bash
py3dblox-viewer
```

**Option 2: Standalone script**
```bash
python view_3dblox.py
```

**Option 3: From Python**
```python
import tkinter as tk
from py3dblox import ThreeDBloxViewer

root = tk.Tk()
viewer = ThreeDBloxViewer(root)
root.mainloop()
```

### Open a File

1. Click `File > Open .3dbx` or `File > Open .3dbv`
2. Select your 3D Block file
3. The 3D visualization will automatically render

### Example Files

Test the viewer with the included example files:

```bash
# From the repository root
py3dblox-viewer
# Then open: src/odb/test/data/example.3dbx
```

## Features

### 3D Visualization
- **Rotate**: Click and drag on the 3D view
- **Zoom**: Use mouse scroll wheel or the zoom tool
- **Pan**: Click the pan icon in the toolbar, then drag
- **Reset View**: Click "Reset View" button

### Chiplet Information
- **Select**: Click "Select" button next to a chiplet name
- **Details Panel**: Shows selected chiplet's:
  - Dimensions (width, height, thickness)
  - Position (x, y, z coordinates)
  - Orientation
  - Regions and their properties
  - External file references

### Visibility Controls
- Use checkboxes next to chiplet names to show/hide individual chiplets
- Toggle grid with "Toggle Grid" button
- Toggle connections with "Toggle Connections" button

### Distance Measurement
1. Click "Measure Distance" button
2. Click two points in the 3D view
3. Distance is displayed in micrometers (μm)

### File Information
- View file metadata in the top-right panel:
  - File name and type
  - Version and unit
  - Number of chiplets and connections

## Toolbar Icons

The matplotlib navigation toolbar provides:
- **Home** (house icon): Reset to default view
- **Back/Forward** (arrows): Navigate view history
- **Pan** (cross arrows): Pan mode
- **Zoom** (magnifying glass): Zoom to rectangle
- **Configure** (sliders): Adjust subplot layout
- **Save** (floppy disk): Export view as image

## Keyboard Shortcuts

- `h` - Home view (reset)
- `p` - Pan mode
- `o` - Zoom mode
- `s` - Save image
- `g` - Toggle grid

## Supported File Formats

### .3dbx Files (Design Assembly)
- Shows complete 3D stack with positioned chiplet instances
- Displays connections between layers
- Supports multiple chiplets at different Z heights

### .3dbv Files (Chiplet Definitions)
- Shows individual chiplet definitions
- Displays regions and boundaries
- Chiplets are stacked vertically for visualization

## Tips

1. **For large designs**: Use visibility checkboxes to hide chiplets and improve performance
2. **To examine details**: Select a chiplet to highlight it and view its properties
3. **To save views**: Use the save button to export the current view as PNG
4. **To measure**: Use the measurement tool to verify spacing between chiplets
5. **Region visualization**: Red outlines show chiplet regions (e.g., bump areas)

## Troubleshooting

### "Could not import the viewer module"
Install matplotlib and numpy:
```bash
pip install matplotlib numpy
```

### Display issues on Linux
If you encounter display issues, ensure you have tkinter installed:
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora/CentOS
sudo dnf install python3-tkinter
```

### File not loading
- Verify the file is a valid `.3dbx` or `.3dbv` file
- Check that included files (referenced in `include:`) are in the correct path
- Review error messages in the terminal

## Architecture

The viewer consists of:
- **Main Window** (`ThreeDBloxViewer`): Tkinter-based GUI
- **3D Renderer**: Matplotlib 3D plotting with interactive controls
- **Data Parser**: Uses py3dblox parser for file loading
- **Interactive Elements**:
  - Chiplet visibility toggles
  - Detail panel with text display
  - Measurement tools
  - Connection visualization

## Color Coding

- Each chiplet is assigned a unique color based on its name
- Selected chiplets are highlighted with:
  - Thicker borders
  - Bold labels
  - Higher opacity
- Connections are shown as dashed blue lines
- Regions are outlined in red

## Performance

The viewer is optimized for typical 3D-IC designs with:
- Up to 10-20 chiplets
- Hundreds of regions
- Multiple connections

For very large designs, consider:
- Hiding unused chiplets
- Reducing the number of visible regions
- Closing and reopening to reset the view

## Contributing

Found a bug or want to add a feature? Please submit issues or pull requests to:
https://github.com/The-OpenROAD-Project/OpenROAD/issues

## License

BSD-3-Clause
Copyright (c) 2019-2025, The OpenROAD Authors
