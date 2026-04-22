# map_jornadas — Requirements & Setup Guide

## Software Requirements

### Python
- **Version:** Python 3.10 or higher
- Required for the `tuple[float, float] | None` type hint syntax used in the script.
- Download: https://www.python.org/downloads/

### Python Packages
Install all dependencies in one command:
```bash
pip install -r requirements.txt
```

| Package    | Min version | Purpose                                                  |
|------------|-------------|----------------------------------------------------------|
| `folium`   | 0.17.0      | Renders interactive Leaflet.js maps as HTML              |
| `pandas`   | 2.0.0       | Reads the Excel file and manipulates tabular data        |
| `openpyxl` | 3.1.0       | Parses named Excel tables (ListObjects) inside .xlsx files |

> The `argparse` and `json` modules are part of the Python standard library and require no separate installation.

### Web Browser
Any modern browser (Chrome, Firefox, Edge, Safari) is needed to open the generated `.html` map file. No internet connection is required to view it — all map tiles are embedded via CDN links resolved at render time.

---

## Hardware Requirements

There are no demanding hardware requirements. The script runs comfortably on any machine capable of running Python.

| Resource | Minimum        | Notes                                                          |
|----------|----------------|----------------------------------------------------------------|
| CPU      | Any            | Processing is single-threaded and lightweight                  |
| RAM      | 256 MB free    | Sufficient for typical datasets (up to ~100k rows)             |
| Disk     | ~50 MB free    | For Python packages; output HTML files are usually under 5 MB  |
| OS       | Windows / macOS / Linux | No platform-specific dependencies                   |

---

## Input Data Requirements

- **File format:** `.xlsx` or `.xlsm` (Excel workbook)
- **Location:** By default, looked up in `~/OneDrive/Documents/`. Configurable via `--dir`, `--excel_filename`, or `--excel_path`.
- **Table:** A named Excel table (Insert → Table in Excel) called `Jornadas` by default. A sheet with that name is also accepted as a fallback.
- **Coordinates column:** A column named `Coords` by default, containing entries in `"latitude,longitude"` format (e.g. `43.2630,−2.9350`). Rows with missing or malformed values are skipped with a warning.

---

## Configuration

Parameters can be set in three ways, listed from highest to lowest priority:

1. **CLI arguments** — e.g. `--excel_filename trips.xlsx --show_heatmap false`
2. **JSON config file** — passed via `--config settings.json`
3. **Built-in defaults** — used for any parameter not specified elsewhere

### All parameters

| Parameter        | Required | Default                    | Description                                                                                 |
|------------------|----------|----------------------------|---------------------------------------------------------------------------------------------|
| `dir`  | Yes      | `~/OneDrive/Documents`     | Folder where the Excel file is located                                                      |
| `excel_filename` | Yes      | `your_file.xlsx`           | Excel filename within `dir`                                                                 |
| `excel_path`     | No       | derived from above         | Full path to the Excel file; overrides the two above                                        |
| `table_name`     | Yes      | `Jornadas`                 | Name of the Excel table or sheet to read                                                    |
| `coords_col`     | No       | `Coords`                   | Column containing `"lat,lon"` coordinate strings                                            |
| `output_map`     | No       | `mapa_jornadas.html`       | Output filename; saved in the same folder as the Excel file                                 |
| `skip_fields`    | No       | `[]`                       | Skip fields to include in pop up markers |
| `show_markers`   | No       | `true`                     | Render a clickable marker for each location                                                 |
| `show_heatmap`   | No       | `true`                     | Render a density heatmap layer                                                              |

---

## Usage Examples

```bash
# Minimal — relies on defaults, only sets the filename
python map_jornadas.py --excel_filename my_trips.xlsx

# Full CLI
python map_jornadas.py \
  --dir ~/Documents \
  --excel_filename my_trips.xlsx \
  --table_name Jornadas \
  --output_map map.html \
  --show_markers true \
  --show_heatmap false

# JSON config file
python map_jornadas.py --config settings.json

# JSON config as base, CLI overrides one value
python map_jornadas.py --config settings.json --show_heatmap false
```

### Example `settings.json`
```json
{
  "dir":  "~/OneDrive/Documents",
  "excel_filename": "my_trips.xlsx",
  "table_name":     "Jornadas",
  "coords_col":     "Coords",
  "output_map":     "mapa_jornadas.html",
  "show_markers":   true,
  "show_heatmap":   true
}
```
