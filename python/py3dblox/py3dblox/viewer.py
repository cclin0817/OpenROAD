# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2019-2025, The OpenROAD Authors

"""3D GUI viewer for 3dblox stacking structures."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Optional
import logging

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

from .parser import parse, parse_dbv, parse_dbx
from .objects import DbxData, DbvData, ChipletInst, ChipletDef


class ThreeDBloxViewer:
    """Main GUI window for 3D Block viewer."""

    def __init__(self, root: tk.Tk):
        """Initialize the viewer.

        Args:
            root: The tkinter root window.
        """
        self.root = root
        self.root.title("3D Blox Stack Viewer")
        self.root.geometry("1400x900")

        # Data storage
        self.data: Optional[DbxData | DbvData] = None
        self.current_file: Optional[Path] = None
        self.chiplet_defs: dict[str, ChipletDef] = {}  # Chiplet definitions (from .3dbv or included files)
        self.chiplet_artists = {}  # Maps chiplet name to artist objects
        self.chiplet_visibility = {}  # Maps chiplet name to visibility state
        self.selected_chiplet: Optional[str] = None
        self.measurement_points = []  # For distance measurement
        self.measurement_mode = False

        # Logger
        self.logger = logging.getLogger('py3dblox.viewer')

        # Setup UI
        self._setup_ui()

    def _setup_ui(self):
        """Setup the user interface."""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open .3dbx", command=lambda: self._open_file('.3dbx'))
        file_menu.add_command(label="Open .3dbv", command=lambda: self._open_file('.3dbv'))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Main container
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Left panel - 3D view
        left_frame = ttk.Frame(main_container)
        main_container.add(left_frame, weight=3)

        # Create matplotlib figure for 3D view
        self.fig = Figure(figsize=(10, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_xlabel('X (μm)')
        self.ax.set_ylabel('Y (μm)')
        self.ax.set_zlabel('Z (μm)')
        self.ax.set_title('3D Stack View')

        # Embed matplotlib in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=left_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Toolbar
        toolbar_frame = ttk.Frame(left_frame)
        toolbar_frame.pack(side=tk.TOP, fill=tk.X)

        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()

        # Control buttons
        control_frame = ttk.Frame(left_frame)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Button(control_frame, text="Reset View", command=self._reset_view).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Toggle Grid", command=self._toggle_grid).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Toggle Connections", command=self._toggle_connections).pack(side=tk.LEFT, padx=2)

        self.measure_btn = ttk.Button(control_frame, text="Measure Distance", command=self._toggle_measurement)
        self.measure_btn.pack(side=tk.LEFT, padx=2)

        self.measure_label = ttk.Label(control_frame, text="")
        self.measure_label.pack(side=tk.LEFT, padx=10)

        # Right panel - Information and controls
        right_frame = ttk.Frame(main_container, width=400)
        main_container.add(right_frame, weight=1)

        # File info section
        info_frame = ttk.LabelFrame(right_frame, text="File Information", padding=10)
        info_frame.pack(fill=tk.X, padx=5, pady=5)

        self.file_info_text = tk.Text(info_frame, height=6, wrap=tk.WORD, state=tk.DISABLED)
        self.file_info_text.pack(fill=tk.X)

        # Chiplet list section
        chiplet_frame = ttk.LabelFrame(right_frame, text="Chiplets", padding=10)
        chiplet_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollable list of chiplets with checkboxes
        chiplet_canvas = tk.Canvas(chiplet_frame)
        scrollbar = ttk.Scrollbar(chiplet_frame, orient=tk.VERTICAL, command=chiplet_canvas.yview)
        self.chiplet_list_frame = ttk.Frame(chiplet_canvas)

        self.chiplet_list_frame.bind(
            "<Configure>",
            lambda e: chiplet_canvas.configure(scrollregion=chiplet_canvas.bbox("all"))
        )

        chiplet_canvas.create_window((0, 0), window=self.chiplet_list_frame, anchor="nw")
        chiplet_canvas.configure(yscrollcommand=scrollbar.set)

        chiplet_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Details section
        details_frame = ttk.LabelFrame(right_frame, text="Selected Chiplet Details", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.details_text = tk.Text(details_frame, height=15, wrap=tk.WORD, state=tk.DISABLED)
        details_scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scrollbar.set)
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind click event for selection
        self.canvas.mpl_connect('button_press_event', self._on_click)

        # Show initial state
        self._update_file_info()

    def _open_file(self, file_type: str):
        """Open a 3dblox file.

        Args:
            file_type: Either '.3dbx' or '.3dbv'
        """
        filetypes = [(f"{file_type.upper()} files", f"*{file_type}"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(title=f"Open {file_type} file", filetypes=filetypes)

        if not filename:
            return

        try:
            self.current_file = Path(filename)
            self.data = parse(filename)
            self.logger.info(f"Loaded file: {filename}")

            # Load chiplet definitions
            self._load_chiplet_defs()

            # Reset state
            self.selected_chiplet = None
            self.measurement_points = []
            self.measurement_mode = False
            self.measure_label.config(text="")

            # Update UI
            self._update_file_info()
            self._update_chiplet_list()
            self._render_3d_view()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")
            self.logger.error(f"Failed to load file: {e}", exc_info=True)

    def _update_file_info(self):
        """Update the file information display."""
        self.file_info_text.config(state=tk.NORMAL)
        self.file_info_text.delete(1.0, tk.END)

        if self.current_file and self.data:
            info = f"File: {self.current_file.name}\n"
            info += f"Type: {type(self.data).__name__}\n"
            info += f"Version: {self.data.header.version}\n"
            info += f"Unit: {self.data.header.unit}\n"
            info += f"Precision: {self.data.header.precision}\n"

            if isinstance(self.data, DbxData):
                info += f"Design: {self.data.design.name}\n"
                info += f"Chiplets: {len(self.data.chiplet_instances)}\n"
                info += f"Connections: {len(self.data.connections)}\n"
            elif isinstance(self.data, DbvData):
                info += f"Chiplet Definitions: {len(self.data.chiplet_defs)}\n"

            self.file_info_text.insert(1.0, info)
        else:
            self.file_info_text.insert(1.0, "No file loaded.\nUse File menu to open a .3dbx or .3dbv file.")

        self.file_info_text.config(state=tk.DISABLED)

    def _load_chiplet_defs(self):
        """Load chiplet definitions from the current data.

        For .3dbv files, use the chiplet_defs directly.
        For .3dbx files, parse included .3dbv files to get chiplet definitions.
        """
        self.chiplet_defs.clear()

        if isinstance(self.data, DbvData):
            # For .3dbv files, use the chiplet definitions directly
            self.chiplet_defs = self.data.chiplet_defs.copy()
        elif isinstance(self.data, DbxData):
            # For .3dbx files, parse included files to get chiplet definitions
            if self.data.header.includes and self.current_file:
                for include_file in self.data.header.includes:
                    try:
                        # Resolve relative paths
                        include_path = self.current_file.parent / include_file
                        if include_path.exists():
                            self.logger.info(f"Loading chiplet definitions from {include_path}")
                            dbv_data = parse_dbv(include_path)
                            self.chiplet_defs.update(dbv_data.chiplet_defs)
                        else:
                            self.logger.warning(f"Included file not found: {include_path}")
                    except Exception as e:
                        self.logger.error(f"Failed to load included file {include_file}: {e}")

    def _update_chiplet_list(self):
        """Update the chiplet list with checkboxes."""
        # Clear existing widgets
        for widget in self.chiplet_list_frame.winfo_children():
            widget.destroy()

        self.chiplet_visibility.clear()

        if not self.data:
            return

        chiplets = []
        if isinstance(self.data, DbxData):
            chiplets = list(self.data.chiplet_instances.keys())
        elif isinstance(self.data, DbvData):
            chiplets = list(self.data.chiplet_defs.keys())

        for i, name in enumerate(chiplets):
            var = tk.BooleanVar(value=True)
            self.chiplet_visibility[name] = var

            checkbox = ttk.Checkbutton(
                self.chiplet_list_frame,
                text=name,
                variable=var,
                command=self._on_visibility_change
            )
            checkbox.grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)

            # Add a select button
            select_btn = ttk.Button(
                self.chiplet_list_frame,
                text="Select",
                width=8,
                command=lambda n=name: self._select_chiplet(n)
            )
            select_btn.grid(row=i, column=1, padx=5, pady=2)

    def _on_visibility_change(self):
        """Handle visibility checkbox changes."""
        self._render_3d_view()

    def _select_chiplet(self, name: str):
        """Select a chiplet and show its details.

        Args:
            name: The chiplet name.
        """
        self.selected_chiplet = name
        self._update_details()
        self._render_3d_view()

    def _update_details(self):
        """Update the details panel with selected chiplet information."""
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)

        if not self.selected_chiplet or not self.data:
            self.details_text.insert(1.0, "No chiplet selected.\nClick on a chiplet in the 3D view or use the Select button.")
            self.details_text.config(state=tk.DISABLED)
            return

        details = f"=== {self.selected_chiplet} ===\n\n"

        if isinstance(self.data, DbxData):
            inst = self.data.chiplet_instances.get(self.selected_chiplet)
            if inst:
                details += f"Reference: {inst.reference}\n"
                details += f"Position: ({inst.loc.x:.2f}, {inst.loc.y:.2f}, {inst.z:.2f}) μm\n"
                details += f"Orientation: {inst.orient}\n"

                # Add chiplet definition details if available
                if inst.reference in self.chiplet_defs:
                    chiplet_def = self.chiplet_defs[inst.reference]
                    details += f"\nChiplet Definition:\n"
                    details += f"  Type: {chiplet_def.type}\n"
                    details += f"  Dimensions: {chiplet_def.design_width:.2f} × {chiplet_def.design_height:.2f} μm\n"
                    details += f"  Thickness: {chiplet_def.thickness:.2f} μm\n"
                    if chiplet_def.regions:
                        details += f"  Regions: {len(chiplet_def.regions)}\n"

                details += f"\nExternal Files:\n"
                if inst.external.verilog_file:
                    details += f"  Verilog: {inst.external.verilog_file}\n"
                if inst.external.sdc_file:
                    details += f"  SDC: {inst.external.sdc_file}\n"
                if inst.external.def_file:
                    details += f"  DEF: {inst.external.def_file}\n"

        elif isinstance(self.data, DbvData):
            chiplet = self.data.chiplet_defs.get(self.selected_chiplet)
            if chiplet:
                details += f"Type: {chiplet.type}\n"
                details += f"Dimensions: {chiplet.design_width:.2f} × {chiplet.design_height:.2f} μm\n"
                details += f"Thickness: {chiplet.thickness:.2f} μm\n"
                details += f"Offset: ({chiplet.offset.x:.2f}, {chiplet.offset.y:.2f}) μm\n"
                details += f"Shrink: {chiplet.shrink}\n"
                details += f"TSV: {chiplet.tsv}\n"

                if chiplet.regions:
                    details += f"\nRegions ({len(chiplet.regions)}):\n"
                    for region_name, region in chiplet.regions.items():
                        details += f"  - {region_name}:\n"
                        details += f"      Side: {region.side}\n"
                        details += f"      Layer: {region.layer}\n"
                        if region.bmap:
                            details += f"      Bump Map: {region.bmap}\n"
                        details += f"      Coordinates: {len(region.coords)} points\n"

                if chiplet.external.lef_files or chiplet.external.tech_lef_files or chiplet.external.def_file:
                    details += f"\nExternal Files:\n"
                    if chiplet.external.tech_lef_files:
                        details += f"  Tech LEF: {', '.join(chiplet.external.tech_lef_files[:2])}\n"
                    if chiplet.external.lef_files:
                        details += f"  LEF: {', '.join(chiplet.external.lef_files[:2])}\n"
                    if chiplet.external.def_file:
                        details += f"  DEF: {chiplet.external.def_file}\n"

        self.details_text.insert(1.0, details)
        self.details_text.config(state=tk.DISABLED)

    def _render_3d_view(self):
        """Render the 3D view of the stack."""
        self.ax.clear()
        self.ax.set_xlabel('X (μm)')
        self.ax.set_ylabel('Y (μm)')
        self.ax.set_zlabel('Z (μm)')
        self.ax.set_title('3D Stack View')

        if not self.data:
            self.canvas.draw()
            return

        self.chiplet_artists.clear()

        if isinstance(self.data, DbxData):
            self._render_dbx_data()
        elif isinstance(self.data, DbvData):
            self._render_dbv_data()

        # Set equal aspect ratio
        self._set_axes_equal()
        self.canvas.draw()

    def _render_dbx_data(self):
        """Render .3dbx data (chiplet instances in a stack)."""
        for name, inst in self.data.chiplet_instances.items():
            # Check visibility
            if name in self.chiplet_visibility and not self.chiplet_visibility[name].get():
                continue

            # Get dimensions from referenced chiplet definition
            width = 1000.0  # Default width
            height = 1000.0  # Default height
            thickness = 100.0  # Default thickness

            if inst.reference in self.chiplet_defs:
                chiplet_def = self.chiplet_defs[inst.reference]
                if chiplet_def.design_width > 0:
                    width = chiplet_def.design_width
                if chiplet_def.design_height > 0:
                    height = chiplet_def.design_height
                if chiplet_def.thickness > 0:
                    thickness = chiplet_def.thickness

            x = inst.loc.x
            y = inst.loc.y
            z = inst.z

            # Create cuboid for chiplet
            color = self._get_chiplet_color(name)
            alpha = 0.9 if name == self.selected_chiplet else 0.6

            vertices, faces = self._create_cuboid(x, y, z, width, height, thickness)

            poly = Poly3DCollection(faces, alpha=alpha, facecolor=color, edgecolor='black', linewidth=1.5 if name == self.selected_chiplet else 0.5)
            self.ax.add_collection3d(poly)

            # Add label
            cx = x + width / 2
            cy = y + height / 2
            cz = z + thickness / 2
            self.ax.text(cx, cy, cz, name, fontsize=9, ha='center', va='center', weight='bold' if name == self.selected_chiplet else 'normal')

            self.chiplet_artists[name] = (poly, width, height, thickness)  # Store dimensions for later use

        # Render connections
        self._render_connections()

    def _render_dbv_data(self):
        """Render .3dbv data (chiplet definitions)."""
        z_offset = 0
        spacing = 50  # Spacing between chiplets in vertical display

        for name, chiplet in self.data.chiplet_defs.items():
            # Check visibility
            if name in self.chiplet_visibility and not self.chiplet_visibility[name].get():
                continue

            x = chiplet.offset.x
            y = chiplet.offset.y
            z = z_offset
            width = chiplet.design_width if chiplet.design_width > 0 else 1000.0
            height = chiplet.design_height if chiplet.design_height > 0 else 1000.0
            thickness = chiplet.thickness if chiplet.thickness > 0 else 100.0

            # Create cuboid for chiplet
            color = self._get_chiplet_color(name)
            alpha = 0.9 if name == self.selected_chiplet else 0.6

            vertices, faces = self._create_cuboid(x, y, z, width, height, thickness)

            poly = Poly3DCollection(faces, alpha=alpha, facecolor=color, edgecolor='black', linewidth=1.5 if name == self.selected_chiplet else 0.5)
            self.ax.add_collection3d(poly)

            # Add label
            cx = x + width / 2
            cy = y + height / 2
            cz = z + thickness / 2
            self.ax.text(cx, cy, cz, name, fontsize=9, ha='center', va='center', weight='bold' if name == self.selected_chiplet else 'normal')

            self.chiplet_artists[name] = (poly, width, height, thickness)  # Store dimensions for later use

            # Render regions
            self._render_regions(chiplet, z, thickness)

            z_offset += thickness + spacing

    def _render_regions(self, chiplet: ChipletDef, z_base: float, thickness: float):
        """Render chiplet regions as colored outlines.

        Args:
            chiplet: The chiplet definition.
            z_base: The base z-coordinate of the chiplet.
            thickness: The thickness of the chiplet.
        """
        for region_name, region in chiplet.regions.items():
            if not region.coords:
                continue

            # Determine z position based on side
            if region.side == 'front':
                z = z_base
            elif region.side == 'back':
                z = z_base + thickness
            else:
                z = z_base + thickness / 2

            # Draw region boundary
            xs = [coord.x for coord in region.coords] + [region.coords[0].x]
            ys = [coord.y for coord in region.coords] + [region.coords[0].y]
            zs = [z] * len(xs)

            self.ax.plot(xs, ys, zs, color='red', linewidth=2, alpha=0.8, label=f"{region_name}")

    def _render_connections(self):
        """Render connections between chiplets."""
        if not isinstance(self.data, DbxData):
            return

        for name, conn in self.data.connections.items():
            # Parse connection endpoints (format: "inst.regions.name")
            try:
                top_parts = conn.top.split('.')
                bot_parts = conn.bot.split('.')

                # Handle virtual connections (indicated by ~)
                if conn.top == '~' or conn.bot == '~':
                    continue

                if len(top_parts) >= 1 and len(bot_parts) >= 1:
                    top_inst_name = top_parts[0]
                    bot_inst_name = bot_parts[0]

                    top_inst = self.data.chiplet_instances.get(top_inst_name)
                    bot_inst = self.data.chiplet_instances.get(bot_inst_name)

                    if top_inst and bot_inst:
                        # Get chiplet dimensions
                        top_dims = self.chiplet_artists.get(top_inst_name)
                        bot_dims = self.chiplet_artists.get(bot_inst_name)

                        # Use center of chiplets, with proper dimensions
                        if top_dims and len(top_dims) == 4:
                            _, top_w, top_h, top_t = top_dims
                        else:
                            top_w, top_h, top_t = 1000.0, 1000.0, 100.0

                        if bot_dims and len(bot_dims) == 4:
                            _, bot_w, bot_h, bot_t = bot_dims
                        else:
                            bot_w, bot_h, bot_t = 1000.0, 1000.0, 100.0

                        # Draw connection line from top of bottom chiplet to bottom of top chiplet
                        x1 = bot_inst.loc.x + bot_w / 2
                        y1 = bot_inst.loc.y + bot_h / 2
                        z1 = bot_inst.z + bot_t  # Top surface of bottom chiplet

                        x2 = top_inst.loc.x + top_w / 2
                        y2 = top_inst.loc.y + top_h / 2
                        z2 = top_inst.z  # Bottom surface of top chiplet

                        self.ax.plot([x1, x2], [y1, y2], [z1, z2],
                                   color='blue', linewidth=2, linestyle='--', alpha=0.7, label=name)
            except Exception as e:
                self.logger.warning(f"Failed to render connection {name}: {e}")

    def _create_cuboid(self, x: float, y: float, z: float, width: float, height: float, depth: float):
        """Create vertices and faces for a cuboid.

        Args:
            x, y, z: Bottom-left-front corner position.
            width: Size in x direction.
            height: Size in y direction.
            depth: Size in z direction (thickness).

        Returns:
            Tuple of (vertices, faces).
        """
        # Define the 8 vertices of the cuboid
        vertices = np.array([
            [x, y, z],
            [x + width, y, z],
            [x + width, y + height, z],
            [x, y + height, z],
            [x, y, z + depth],
            [x + width, y, z + depth],
            [x + width, y + height, z + depth],
            [x, y + height, z + depth]
        ])

        # Define the 6 faces (each face is defined by 4 vertex indices)
        faces = [
            [vertices[0], vertices[1], vertices[2], vertices[3]],  # Bottom
            [vertices[4], vertices[5], vertices[6], vertices[7]],  # Top
            [vertices[0], vertices[1], vertices[5], vertices[4]],  # Front
            [vertices[2], vertices[3], vertices[7], vertices[6]],  # Back
            [vertices[0], vertices[3], vertices[7], vertices[4]],  # Left
            [vertices[1], vertices[2], vertices[6], vertices[5]]   # Right
        ]

        return vertices, faces

    def _get_chiplet_color(self, name: str) -> tuple:
        """Get a color for a chiplet based on its name.

        Args:
            name: The chiplet name.

        Returns:
            RGB tuple.
        """
        # Simple hash-based color generation
        hash_val = hash(name)
        r = ((hash_val & 0xFF0000) >> 16) / 255.0
        g = ((hash_val & 0x00FF00) >> 8) / 255.0
        b = (hash_val & 0x0000FF) / 255.0

        # Ensure colors are not too dark
        r = max(0.3, r)
        g = max(0.3, g)
        b = max(0.3, b)

        return (r, g, b)

    def _set_axes_equal(self):
        """Set equal aspect ratio for 3D plot."""
        if not self.data:
            return

        # Get all vertices from rendered objects
        all_coords = []

        if isinstance(self.data, DbxData):
            for inst in self.data.chiplet_instances.values():
                all_coords.extend([
                    [inst.loc.x, inst.loc.y, inst.z],
                    [inst.loc.x + 1000, inst.loc.y + 1000, inst.z + 100]
                ])
        elif isinstance(self.data, DbvData):
            z = 0
            for chiplet in self.data.chiplet_defs.values():
                w = chiplet.design_width if chiplet.design_width > 0 else 1000.0
                h = chiplet.design_height if chiplet.design_height > 0 else 1000.0
                t = chiplet.thickness if chiplet.thickness > 0 else 100.0
                all_coords.extend([
                    [chiplet.offset.x, chiplet.offset.y, z],
                    [chiplet.offset.x + w, chiplet.offset.y + h, z + t]
                ])
                z += t + 50

        if all_coords:
            all_coords = np.array(all_coords)
            max_range = np.array([
                all_coords[:, 0].max() - all_coords[:, 0].min(),
                all_coords[:, 1].max() - all_coords[:, 1].min(),
                all_coords[:, 2].max() - all_coords[:, 2].min()
            ]).max() / 2.0

            mid_x = (all_coords[:, 0].max() + all_coords[:, 0].min()) * 0.5
            mid_y = (all_coords[:, 1].max() + all_coords[:, 1].min()) * 0.5
            mid_z = (all_coords[:, 2].max() + all_coords[:, 2].min()) * 0.5

            self.ax.set_xlim(mid_x - max_range, mid_x + max_range)
            self.ax.set_ylim(mid_y - max_range, mid_y + max_range)
            self.ax.set_zlim(mid_z - max_range, mid_z + max_range)

    def _reset_view(self):
        """Reset the 3D view to default angle."""
        self.ax.view_init(elev=20, azim=45)
        self.canvas.draw()

    def _toggle_grid(self):
        """Toggle grid visibility."""
        self.ax.grid(not self.ax.get_grid())
        self.canvas.draw()

    def _toggle_connections(self):
        """Toggle connection visibility."""
        # Re-render to toggle connections
        self._render_3d_view()

    def _toggle_measurement(self):
        """Toggle distance measurement mode."""
        self.measurement_mode = not self.measurement_mode

        if self.measurement_mode:
            self.measure_btn.config(text="Cancel Measurement")
            self.measure_label.config(text="Click two points to measure distance")
            self.measurement_points = []
        else:
            self.measure_btn.config(text="Measure Distance")
            self.measure_label.config(text="")
            self.measurement_points = []
            self._render_3d_view()

    def _on_click(self, event):
        """Handle click events on the 3D canvas.

        Args:
            event: The matplotlib mouse event.
        """
        if event.inaxes != self.ax:
            return

        # Measurement mode
        if self.measurement_mode and event.button == 1:
            # Get clicked 3D point (approximate)
            if hasattr(event, 'xdata') and hasattr(event, 'ydata'):
                # This is a simplified approach - proper 3D picking is complex
                # For now, just use x, y and estimate z from view
                point = (event.xdata, event.ydata, 0)  # Simplified
                self.measurement_points.append(point)

                if len(self.measurement_points) == 2:
                    # Calculate distance
                    p1, p2 = self.measurement_points
                    dist = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2 + (p2[2] - p1[2])**2)
                    self.measure_label.config(text=f"Distance: {dist:.2f} μm")

                    # Draw measurement line
                    self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]],
                               color='green', linewidth=2, marker='o')
                    self.canvas.draw()

                    # Reset measurement mode
                    self.measurement_mode = False
                    self.measure_btn.config(text="Measure Distance")

        # Selection mode (simplified - clicking in the general area)
        # In a full implementation, this would use proper 3D picking
        # For now, skip automatic selection on click in 3D view


def main():
    """Run the 3D Block viewer application."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(name)s - %(message)s'
    )

    root = tk.Tk()
    app = ThreeDBloxViewer(root)
    root.mainloop()


if __name__ == '__main__':
    main()
