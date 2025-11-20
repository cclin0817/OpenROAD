# 3D Blox Viewer Test Cases

This directory contains test files for validating the 3D GUI Viewer functionality.

## Test Files

### Chiplet Definition Files (.3dbv)

1. **chiplets.3dbv** - Multi-chiplet definitions
   - Defines 3 different chiplets: CPU, Memory, IO_Die
   - Used by .3dbx files as included reference
   - Tests: Different types (die, interposer), various dimensions, multiple regions

2. **single_chiplet.3dbv** - Single detailed chiplet
   - One chiplet (TestChip) with 4 regions
   - Tests: Region rendering, seal rings, complex geometry

### Stack Assembly Files (.3dbx)

3. **simple_stack.3dbx** - Basic 2-chiplet stack
   - CPU + Memory vertical stack
   - 1 connection between layers
   - Tests: Basic stacking, simple connections, chiplet reference resolution

4. **complex_stack.3dbx** - Multi-layer heterogeneous stack
   - 5 chiplets: 1 IO base, 2 CPUs, 2 Memory chips
   - 4 inter-layer connections
   - Tests: Complex stacking, multiple connections, different orientations

## Running Tests

### Automatic Validation

Run the test script to validate all files:

```bash
cd test_cases
python3 test_viewer.py
```

This will:
- Parse all test files
- Verify data integrity
- Check chiplet reference resolution
- Print detailed usage instructions

### Manual GUI Testing

Launch the viewer and load test files:

```bash
# Option 1: Using the launcher script
cd test_cases
python3 ../view_3dblox.py

# Option 2: After installation
pip install -e "../[viewer]"
py3dblox-viewer
```

Then use File > Open to load test files.

## Test Scenarios

### Scenario A: Single Chiplet View
**File**: single_chiplet.3dbv

**Steps**:
1. Load the file
2. Verify chiplet dimensions: 2000 × 2500 × 200 μm
3. Check that 4 regions are visible (red outlines)
4. Select chiplet and verify details panel

**Expected**:
- One colored 3D box
- 4 red region boundaries
- Details show type, dimensions, 4 regions

### Scenario B: Simple Stack
**File**: simple_stack.3dbx

**Steps**:
1. Load the file
2. Verify 2 chiplets at different Z heights:
   - cpu_0 at Z=0 (bottom)
   - mem_0 at Z=50 (top)
3. Check dimensions match chiplet definitions:
   - CPU: 1200 × 1500 × 50 μm
   - Memory: 800 × 1000 × 75 μm
4. Verify 1 blue connection line between chiplets
5. Select cpu_0 and check details include:
   - Position: (150, 150, 0)
   - Reference: CPU
   - Chiplet Definition with actual dimensions

**Expected**:
- 2 colored 3D boxes at different heights
- 1 blue dashed line (connection)
- Actual dimensions (not 1000×1000×100 placeholders)
- Details panel shows both instance and chiplet definition info

### Scenario C: Complex Multi-Layer Stack
**File**: complex_stack.3dbx

**Steps**:
1. Load the file
2. Verify 5 chiplets:
   - io_base at Z=0 (base layer)
   - cpu_0 at Z=100
   - cpu_1 at Z=150 (inverted, MZ orientation)
   - mem_0 at Z=225 (rotated R90)
   - mem_1 at Z=225 (rotated R270)
3. Verify 4 connection lines
4. Test visibility controls:
   - Uncheck mem_0 and mem_1
   - Verify only 3 chiplets visible
   - Re-check to restore
5. Test measurement between chiplets
6. Rotate view to see all layers

**Expected**:
- 5 chiplets in a multi-tier stack
- 4 blue connection lines
- Different orientations visible
- All dimensions from chiplet definitions
- Visibility controls work

### Scenario D: Multiple Chiplet Definitions
**File**: chiplets.3dbv

**Steps**:
1. Load the file
2. Verify 3 chiplets stacked vertically (viewer arranges them for visualization)
3. Check each chiplet has different dimensions
4. Verify region boundaries (red lines):
   - CPU: 2 regions
   - Memory: 1 region
   - IO_Die: 1 region
5. Select each and compare details

**Expected**:
- 3 chiplets shown in vertical arrangement
- Different sizes visible
- Region outlines on appropriate surfaces
- Each chiplet has correct number of regions

## Validation Checklist

Use this checklist when testing the viewer:

- [ ] All test files load without errors
- [ ] Chiplets render as colored 3D boxes
- [ ] Dimensions are accurate (from chiplet definitions, not placeholders)
- [ ] Regions appear as red boundary lines
- [ ] Connections appear as blue dashed lines (in .3dbx files)
- [ ] Details panel shows complete information
- [ ] Instance info includes chiplet definition details (.3dbx)
- [ ] Show/hide checkboxes work
- [ ] Multiple chiplets can be hidden/shown independently
- [ ] Interactive controls work:
  - [ ] Rotate (click and drag)
  - [ ] Zoom (scroll wheel)
  - [ ] Pan (toolbar button)
  - [ ] Reset view button
- [ ] Measurement tool works
- [ ] No Python errors/warnings in console

## Bug Fixes Verified

The following bugs have been fixed and should be verified:

1. **Removed unused import** (`matplotlib.pyplot`)
   - No impact on functionality
   - Cleaner code

2. **Load chiplet definitions from included files**
   - .3dbx files now load chiplet definitions from included .3dbv files
   - Verify: simple_stack.3dbx and complex_stack.3dbx show actual dimensions
   - Check: Details panel shows "Chiplet Definition" section for instances

3. **Use actual dimensions instead of placeholders**
   - Old behavior: All chiplets rendered as 1000×1000×100
   - New behavior: Actual dimensions from chiplet definitions
   - Verify: CPU (1200×1500×50), Memory (800×1000×75), IO_Die (1500×1800×100)

4. **Fix connection rendering**
   - Old behavior: Hardcoded offsets (500, 500, 100)
   - New behavior: Uses actual chiplet dimensions and centers
   - Verify: Connections start/end at chiplet centers, not arbitrary points

5. **Handle virtual connections**
   - Connections with `~` (virtual) are now skipped
   - Verify: complex_stack.3dbx connection "soc_to_virtual" doesn't crash viewer

## File Specifications

### chiplets.3dbv
- **Chiplets**: 3
- **Total Regions**: 4
- **Dimensions**:
  - CPU: 1200 × 1500 × 50 μm, 2 regions
  - Memory: 800 × 1000 × 75 μm, 1 region
  - IO_Die: 1500 × 1800 × 100 μm, 1 region

### single_chiplet.3dbv
- **Chiplets**: 1
- **Total Regions**: 4
- **Dimensions**:
  - TestChip: 2000 × 2500 × 200 μm, 4 regions

### simple_stack.3dbx
- **Design**: SimpleStack
- **Instances**: 2 (cpu_0, mem_0)
- **Connections**: 1
- **Includes**: chiplets.3dbv
- **Z Range**: 0 to 125 μm

### complex_stack.3dbx
- **Design**: ComplexHeteroStack
- **Instances**: 5 (io_base, cpu_0, cpu_1, mem_0, mem_1)
- **Connections**: 4
- **Includes**: chiplets.3dbv
- **Z Range**: 0 to 300 μm
- **Orientations**: R0, MZ, R90, R270

## Troubleshooting

### Parser Errors
If test_viewer.py reports parsing errors:
- Check YAML syntax in test files
- Verify include paths are correct
- Ensure chiplets.3dbv exists (required by .3dbx files)

### Viewer Doesn't Open
- Ensure matplotlib and numpy are installed: `pip install matplotlib numpy`
- Check for tkinter: `python3 -c "import tkinter"`
  - Linux: `sudo apt-get install python3-tk`
  - Mac: Usually included with Python
  - Windows: Usually included with Python

### Chiplets Not Visible
- Check visibility checkboxes are checked
- Try "Reset View" button
- Zoom out (scroll wheel)
- Verify file loaded successfully (check terminal for errors)

### Wrong Dimensions
If chiplets show as 1000×1000×100:
- Verify the bug fixes are applied (check viewer.py has `_load_chiplet_defs` method)
- Check include paths are correct in .3dbx files
- Verify chiplets.3dbv exists in same directory as .3dbx files

## Contributing

To add new test cases:
1. Create .3dbv and/or .3dbx files in this directory
2. Add test scenario to test_viewer.py
3. Document in this README
4. Verify all existing tests still pass

## License

BSD-3-Clause
Copyright (c) 2019-2025, The OpenROAD Authors
