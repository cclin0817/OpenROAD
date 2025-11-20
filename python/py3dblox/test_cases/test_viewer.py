#!/usr/bin/env python3
"""
Test script for the 3D Blox GUI Viewer.

This script validates the viewer functionality and provides test cases.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
test_dir = Path(__file__).parent
sys.path.insert(0, str(test_dir.parent))

def test_parser():
    """Test that the parser can load all test files."""
    print("=" * 60)
    print("TESTING PARSER FUNCTIONALITY")
    print("=" * 60)

    from py3dblox import parse_dbv, parse_dbx

    test_files = [
        ("chiplets.3dbv", "Chiplet Definitions"),
        ("single_chiplet.3dbv", "Single Chiplet"),
        ("simple_stack.3dbx", "Simple Stack"),
        ("complex_stack.3dbx", "Complex Stack"),
    ]

    all_passed = True

    for filename, description in test_files:
        filepath = test_dir / filename
        print(f"\n{description} ({filename}):")
        print("-" * 60)

        try:
            if filename.endswith('.3dbv'):
                data = parse_dbv(filepath)
                print(f"  ✓ Parsed successfully")
                print(f"  - Version: {data.header.version}")
                print(f"  - Unit: {data.header.unit}")
                print(f"  - Chiplet Definitions: {len(data.chiplet_defs)}")

                for name, chiplet in data.chiplet_defs.items():
                    print(f"    • {name}:")
                    print(f"        Type: {chiplet.type}")
                    print(f"        Size: {chiplet.design_width} × {chiplet.design_height} μm")
                    print(f"        Thickness: {chiplet.thickness} μm")
                    print(f"        Regions: {len(chiplet.regions)}")

            elif filename.endswith('.3dbx'):
                data = parse_dbx(filepath)
                print(f"  ✓ Parsed successfully")
                print(f"  - Design: {data.design.name}")
                print(f"  - Instances: {len(data.chiplet_instances)}")
                print(f"  - Connections: {len(data.connections)}")
                print(f"  - Includes: {data.header.includes}")

                for name, inst in data.chiplet_instances.items():
                    print(f"    • {name}:")
                    print(f"        Reference: {inst.reference}")
                    print(f"        Position: ({inst.loc.x}, {inst.loc.y}, {inst.z}) μm")
                    print(f"        Orientation: {inst.orient}")

                # Test chiplet definition loading (simulate viewer behavior)
                chiplet_defs = {}
                if data.header.includes:
                    for include in data.header.includes:
                        include_path = filepath.parent / include
                        if include_path.exists():
                            dbv_data = parse_dbv(include_path)
                            chiplet_defs.update(dbv_data.chiplet_defs)

                print(f"  - Loaded chiplet definitions: {list(chiplet_defs.keys())}")

                # Validate references
                missing_refs = []
                for inst_name, inst in data.chiplet_instances.items():
                    if inst.reference not in chiplet_defs:
                        missing_refs.append((inst_name, inst.reference))

                if missing_refs:
                    print(f"  ⚠ Warning: Missing chiplet definitions:")
                    for inst_name, ref in missing_refs:
                        print(f"      - Instance '{inst_name}' references '{ref}'")
                else:
                    print(f"  ✓ All instance references resolved")

        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL PARSER TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 60)

    return all_passed


def print_usage_instructions():
    """Print instructions for using the GUI viewer."""
    print("\n" + "=" * 60)
    print("GUI VIEWER USAGE INSTRUCTIONS")
    print("=" * 60)
    print("""
To test the 3D GUI Viewer, you have two options:

OPTION 1: Command-line tool (after installation)
----------------------------------------------
  $ pip install -e ".[viewer]"
  $ py3dblox-viewer

OPTION 2: Direct script execution
----------------------------------
  $ python3 ../view_3dblox.py

Once the GUI opens:

1. LOAD A FILE:
   - Click "File" > "Open .3dbx" or "Open .3dbv"
   - Navigate to one of the test files:
     • single_chiplet.3dbv - Single chiplet with 4 regions
     • chiplets.3dbv - Three chiplet definitions
     • simple_stack.3dbx - CPU + Memory stack (2 chiplets)
     • complex_stack.3dbx - Multi-layer stack (5 chiplets)

2. EXPLORE THE 3D VIEW:
   - Rotate: Click and drag on the 3D plot
   - Zoom: Use mouse scroll wheel
   - Pan: Click the pan icon in toolbar, then drag
   - Reset: Click "Reset View" button

3. SELECT CHIPLETS:
   - Click "Select" button next to chiplet names
   - View details in the "Selected Chiplet Details" panel
   - Check/uncheck boxes to show/hide chiplets

4. MEASURE DISTANCES:
   - Click "Measure Distance" button
   - Click two points in the 3D view
   - Distance will be displayed in micrometers

5. VIEW CONNECTIONS:
   - Load a .3dbx file (simple_stack or complex_stack)
   - Blue dashed lines show connections between chiplets
   - Red lines show region boundaries

TEST SCENARIOS:
--------------
A. Basic Viewing:
   1. Load "single_chiplet.3dbv"
   2. Verify chiplet is displayed with 4 region boundaries (red lines)
   3. Select the chiplet and check details panel shows:
      - Type, dimensions, thickness
      - 4 regions with coordinates

B. Stack Visualization:
   1. Load "simple_stack.3dbx"
   2. Verify 2 chiplets are displayed at different Z heights
   3. Verify actual dimensions (not placeholders):
      - CPU: 1200 × 1500 × 50 μm
      - Memory: 800 × 1000 × 75 μm
   4. Verify 1 connection (blue dashed line) between chiplets
   5. Select each chiplet and verify details include:
      - Instance position and orientation
      - Reference chiplet definition with dimensions

C. Complex Stack:
   1. Load "complex_stack.3dbx"
   2. Verify 5 chiplets are displayed
   3. Verify 4 connections between layers
   4. Test visibility controls:
      - Uncheck "mem_0" and "mem_1"
      - Verify only CPU and IO chiplets are visible
      - Re-check to restore visibility
   5. Test measurement tool between chiplets

D. Chiplet Definitions:
   1. Load "chiplets.3dbv"
   2. Verify 3 chiplets stacked vertically for viewing
   3. Each should show its regions as red outlines
   4. Select each and verify region counts:
      - CPU: 2 regions
      - Memory: 1 region
      - IO_Die: 1 region

EXPECTED BEHAVIOR:
-----------------
✓ Files load without errors
✓ Chiplets render as colored 3D boxes
✓ Dimensions match the test file specifications
✓ Connections appear as blue dashed lines
✓ Regions appear as red boundary lines
✓ Details panel updates when selecting chiplets
✓ Show/hide checkboxes work correctly
✓ All interactive controls (rotate, zoom, pan) work
✓ Measurement tool calculates distances

KNOWN LIMITATIONS:
-----------------
• Distance measurement uses 2D projection (Z=0)
• Click-to-select in 3D view is not implemented
  (use the "Select" buttons instead)

""")
    print("=" * 60)


def main():
    """Run all tests and print instructions."""
    # Run parser tests
    parser_passed = test_parser()

    # Print usage instructions
    print_usage_instructions()

    # Print test file summary
    print("\nTEST FILES SUMMARY:")
    print("-" * 60)
    print(f"Directory: {test_dir}")
    print("\nAvailable test files:")
    for filepath in sorted(test_dir.glob("*.3db*")):
        print(f"  • {filepath.name}")
    print("-" * 60)

    if not parser_passed:
        sys.exit(1)

    print("\n✓ Ready to test GUI viewer!")
    print(f"  Change to directory: cd {test_dir}")
    print(f"  Run viewer: python3 ../view_3dblox.py")
    print()


if __name__ == '__main__':
    main()
