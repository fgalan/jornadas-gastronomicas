#
# Licensed under AGPLv3. See LICENCE file in repository root
#
# Author: Pedro José Navarro

"""
map_jornadas.py  –  Plot geo-coordinates from an Excel table onto a folium map.

Configuration priority (highest → lowest):
  1. Individual CLI arguments (--excel_filename, --table_name, …)
  2. JSON config file passed via --config
  3. Built-in defaults

Usage examples
--------------
# Use a JSON config file:
  python map_jornadas.py --config settings.json

# Pass parameters directly on the command line:
  python map_jornadas.py --excel_filename trips.xlsx --show_heatmap false

# Mix both (CLI overrides JSON):
  python map_jornadas.py --config settings.json --show_markers false

JSON config format (all keys optional):
  {
    "dir":  "~/OneDrive/Documents",
    "excel_filename": "trips.xlsx",
    "excel_path":     "~/OneDrive/Documents/trips.xlsx",
    "table_name":     "Jornadas",
    "coords_col":     "Coords",
    "output_map":     "mapa_jornadas.html",
    "skip_fields":    ["Elector", "Asistentes"],
    "show_markers":   true,
    "show_heatmap":   true
  }
"""

import argparse
import json
import os
import sys

import folium
from folium.plugins import HeatMap
import pandas as pd
import openpyxl


# ── Built-in defaults ──────────────────────────────────────────────────────────
DEFAULTS = {
    "dir":  os.path.expanduser("~/OneDrive/Documents"),
    "excel_filename": "your_file.xlsx",
    "excel_path":     None,   # derived from dir + excel_filename if not set
    "table_name":     "Jornadas",
    "coords_col":     "Coords",
    "output_map":     "mapa_jornadas.html",
    "show_markers":   True,
    "show_heatmap":   True,
}
# ───────────────────────────────────────────────────────────────────────────────


def parse_bool(value: str) -> bool:
    """Accept true/false/1/0/yes/no (case-insensitive) from CLI strings."""
    if isinstance(value, bool):
        return value
    if value.lower() in ("true", "1", "yes"):
        return True
    if value.lower() in ("false", "0", "no"):
        return False
    raise argparse.ArgumentTypeError(f"Boolean value expected, got: {value!r}")


def load_config(config_path: str) -> dict:
    """Load and return a JSON config file, expanding ~ in path values."""
    with open(config_path) as f:
        data = json.load(f)
    # Expand ~ in any string values
    for key, val in data.items():
        if isinstance(val, str):
            data[key] = os.path.expanduser(val)
    return data


def build_config() -> dict:
    """
    Merge defaults → JSON config → CLI args, in increasing priority order.
    Returns a fully resolved config dict.
    """
    parser = argparse.ArgumentParser(
        description="Plot geo-coordinates from an Excel table onto a folium map.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--config", metavar="FILE",
        help="Path to a JSON config file. Individual CLI args override its values.",
    )
    parser.add_argument("--dir",  metavar="DIR",
                        help="Path to the folder where the excel file is placed. Using '~' for home directories is allowed.")
    parser.add_argument("--excel_filename", metavar="FILE",
                        help="Excel filename (looked up inside 'dir').")
    parser.add_argument("--excel_path",     metavar="PATH",
                        help="Full path to the Excel file (overrides dir + excel_filename).")
    parser.add_argument("--table_name",     metavar="NAME",
                        help="Name of the Excel table or sheet to read.")
    parser.add_argument("--coords_col",     metavar="COL",
                        help='Column containing "lat,lon" coordinates. '
                             f'(default: {DEFAULTS["coords_col"]})')
    parser.add_argument("--output_map",     metavar="FILE",
                        help="Output HTML filename, saved next to the Excel file. "
                             f'(default: {DEFAULTS["output_map"]})')
    parser.add_argument("--skip_fields",    metavar="FIELDS", type=str,
                        help="List of comma-separated column names to exclude from marker popups.")
    parser.add_argument("--show_markers",   metavar="BOOL", type=parse_bool,
                        help=f'Show individual markers. true/false (default: {DEFAULTS["show_markers"]})')
    parser.add_argument("--show_heatmap",   metavar="BOOL", type=parse_bool,
                        help=f'Show heatmap layer. true/false (default: {DEFAULTS["show_heatmap"]})')

    args = parser.parse_args()

    # Start from built-in defaults
    cfg = dict(DEFAULTS)

    # From comma separted to array of strings in skip_fields
    if args.skip_fields:
        cfg["skip_fields"] = [field.strip() for field in args.skip_fields.split(",") if field.strip()]

    # Layer JSON config on top
    if args.config:
        json_cfg = load_config(args.config)
        cfg.update(json_cfg)

    # Layer explicit CLI args on top (only those the user actually provided)
    cli_overrides = {
        key: val for key, val in vars(args).items()
        if key != "config" and val is not None
    }
    cfg.update(cli_overrides)

    # Derive excel_path if not explicitly set
    if not cfg["excel_path"]:
        cfg["excel_path"] = os.path.join(
            os.path.expanduser(cfg["dir"]),
            cfg["excel_filename"],
        )
    else:
        cfg["excel_path"] = os.path.expanduser(cfg["excel_path"])

    return cfg



def find_excel_file(path: str) -> str:
    if os.path.isfile(path):
        return path
    docs_dir = os.path.dirname(path)
    if os.path.isdir(docs_dir):
        xlsx_files = [f for f in os.listdir(docs_dir) if f.endswith((".xlsx", ".xlsm"))]
        if xlsx_files:
            print(f"Excel files found in {docs_dir}:")
            for f in xlsx_files:
                print(f"  • {f}")
    sys.exit(f"\n❌  File not found: {path}\n"
             f"    Set --excel_filename (or --excel_path) to the correct value.")


def load_table(excel_path: str, table_name: str) -> pd.DataFrame:
    
    wb = openpyxl.load_workbook(excel_path, data_only=True, read_only=False)

    for ws in wb.worksheets:
        for tbl in ws.tables.values():
            if tbl.name == table_name:
                data = ws[tbl.ref]
                rows = [[cell.value for cell in row] for row in data]
                headers, *body = rows
                return pd.DataFrame(body, columns=headers)

    wb.close()
    all_sheets = pd.read_excel(excel_path, sheet_name=None)
    if table_name in all_sheets:
        return all_sheets[table_name]

    sys.exit(f"\n❌  Table or sheet named '{table_name}' not found in {excel_path}.\n"
             f"    Available sheets: {list(all_sheets.keys())}")


def parse_coords(value) -> tuple[float, float] | None:
    if pd.isna(value) or str(value).strip() == "":
        return None
    try:
        parts = str(value).split(",")
        return float(parts[0].strip()), float(parts[1].strip())
    except (ValueError, IndexError):
        return None


def build_map(df: pd.DataFrame, coords_col: str,
              show_markers: bool, show_heatmap: bool, skip_fields: list[str]) -> folium.Map:
    if not show_markers and not show_heatmap:
        sys.exit("❌  Both show_markers and show_heatmap are False. Enable at least one.")

    points = []
    skipped = 0

    for idx, row in df.iterrows():
        result = parse_coords(row.get(coords_col))
        if result is None:
            # print(f"skipped index: {idx}")
            skipped += 1
            continue
        lat, lon = result
        popup_html = "<br>".join(
            f"<b>{col}:</b> {row[col]}"
            for col in df.columns
            if col not in skip_fields and col != coords_col and pd.notna(row[col])
        )
        points.append((lat, lon, popup_html or f"Punto {idx}"))

    if not points:
        sys.exit(f"❌  No valid coordinates found in column '{coords_col}'.")
    if skipped:
        print(f"⚠️   Skipped {skipped} row(s) with missing or invalid coordinates.")

    avg_lat = sum(p[0] for p in points) / len(points)
    avg_lon = sum(p[1] for p in points) / len(points)

    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=7, tiles="OpenStreetMap")

    if show_markers:
        marker_group = folium.FeatureGroup(name="📍 Markers", show=True)
        for lat, lon, popup_html in points:
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"({lat:.5f}, {lon:.5f})",
                icon=folium.Icon(color="blue", icon="map-marker", prefix="fa"),
            ).add_to(marker_group)
        marker_group.add_to(m)

    if show_heatmap:
        heat_data = [[lat, lon] for lat, lon, _ in points]
        heatmap_group = folium.FeatureGroup(name="🌡️ Heatmap", show=True)
        HeatMap(
            heat_data,
            min_opacity=0.4,
            radius=25,
            blur=15,
            gradient={0.2: "blue", 0.5: "lime", 0.8: "orange", 1.0: "red"},
        ).add_to(heatmap_group)
        heatmap_group.add_to(m)

    # Layer control (only useful when both layers are present)
    if show_markers and show_heatmap:
        folium.LayerControl(collapsed=False).add_to(m)

    m.fit_bounds([[p[0], p[1]] for p in points])
    return m


def main():
    cfg = build_config()

    excel_path = find_excel_file(cfg["excel_path"])
    print(f"📂  Loading '{cfg['table_name']}' from:\n    {excel_path}")

    df = load_table(excel_path, cfg["table_name"])
    print(f"✅  Loaded {len(df)} rows. Columns: {list(df.columns)}")

    if cfg["coords_col"] not in df.columns:
        sys.exit(f"\n❌  Column '{cfg['coords_col']}' not found.\n"
                 f"    Available columns: {list(df.columns)}")

    modes = []
    if cfg["show_markers"]: modes.append("markers")
    if cfg["show_heatmap"]:  modes.append("heatmap")
    print(f"🗺️   Rendering: {' + '.join(modes)}")

    output_path = os.path.join(os.path.dirname(excel_path), cfg["output_map"])
    m = build_map(df, cfg["coords_col"], cfg["show_markers"], cfg["show_heatmap"], cfg["skip_fields"])
    m.save(output_path)
    print(f"✅  Map saved → {output_path}")
    print("    Open it in any web browser to view your points.")


if __name__ == "__main__":
    main()
