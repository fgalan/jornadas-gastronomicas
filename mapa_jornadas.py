#
# Licensed under AGPLv3. See LICENCE file in repository root
#
# Author: Pedro José Navarro

import pandas as pd
import folium
from folium.plugins import HeatMap
import os
import sys

# ── Configuration ──────────────────────────────────────────────────────────────
ONEDRIVE_DOCS  = os.path.expanduser("~/OneDrive/Documents")
EXCEL_FILENAME = "JornadasGastronomicas.xlsx"          
EXCEL_PATH     = os.path.join(ONEDRIVE_DOCS, EXCEL_FILENAME)
TABLE_NAME     = "Jornadas"                # Named table inside the workbook
COORDS_COL     = "Coords"                  # Column with "lat,lon" values
OUTPUT_MAP     = "mapa_jornadas.html"      # saved next to the Excel file

# ── Map mode ───────────────────────────────────────────────────────────────────
# Set either or both to True:
SHOW_MARKERS = True
SHOW_HEATMAP = True
# ───────────────────────────────────────────────────────────────────────────────


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
             f"    Update EXCEL_FILENAME at the top of this script and try again.")


def load_table(excel_path: str, table_name: str) -> pd.DataFrame:
    import openpyxl
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
              show_markers: bool, show_heatmap: bool) -> folium.Map:
    if not show_markers and not show_heatmap:
        sys.exit("❌  Both SHOW_MARKERS and SHOW_HEATMAP are False. Enable at least one.")

    points = []
    skipped = 0

    for idx, row in df.iterrows():
        result = parse_coords(row.get(coords_col))
        if result is None:
            print(f"skipped index: {idx}")
            skipped += 1
            continue
        lat, lon = result
        popup_html = "<br>".join(
            f"<b>{col}:</b> {row[col]}"
            for col in df.columns
            if col != coords_col and pd.notna(row[col])
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
    excel_path = find_excel_file(EXCEL_PATH)
    print(f"📂  Loading '{TABLE_NAME}' from:\n    {excel_path}")

    df = load_table(excel_path, TABLE_NAME)
    print(f"✅  Loaded {len(df)} rows. Columns: {list(df.columns)}")

    if COORDS_COL not in df.columns:
        sys.exit(f"\n❌  Column '{COORDS_COL}' not found.\n"
                 f"    Available columns: {list(df.columns)}")

    modes = []
    if SHOW_MARKERS: modes.append("markers")
    if SHOW_HEATMAP: modes.append("heatmap")
    print(f"🗺️   Rendering: {' + '.join(modes)}")

    output_path = os.path.join(os.path.dirname(excel_path), OUTPUT_MAP)
    m = build_map(df, COORDS_COL, SHOW_MARKERS, SHOW_HEATMAP)
    m.save(output_path)
    print(f"✅  Map saved → {output_path}")
    print("    Open it in any web browser to view your points.")


if __name__ == "__main__":
    main()