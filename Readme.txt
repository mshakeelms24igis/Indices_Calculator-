# Spectral Indices Calculator

## Overview
The **Spectral Indices Calculator** is a Python-based desktop application developed using PyQt5 for geospatial data visualization and analysis. The application enables users to perform operations on raster and vector data, calculate spectral indices (NDVI, NDWI, NDBI), and manage geospatial data efficiently.

---

## Features
- **Raster and Shapefile Upload**: Import GeoTIFF files and shapefiles for analysis.

- **Spectral Indices Calculations**:
  - NDVI (Normalized Difference Vegetation Index)
  - NDWI (Normalized Difference Water Index)
  - NDBI (Normalized Difference Built-up Index)

- **Buffer Tool**: Generate buffer zones around vector geometries.
- **Raster Clipping**: Clip raster data using vector geometries.

- **Data Visualization**:
  - View raster data in grayscale or color.
  - Visualize shapefiles on an interactive map (Folium) or a GUI (Matplotlib).

- **Database Integration**:
  - Connect to a PostgreSQL/PostGIS database.
  - Import and visualize geospatial data from PostGIS.

- **Export**: Save processed data to disk (shapefiles or GeoTIFF).
---

## Installation
1. Clone this repository or download the source files.
2. Ensure Python 3.8+ is installed on your system.
3. Install the required libraries using `pip`:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python main_code.py
   ```

---

## Requirements
- Python 3.8+
- PyQt5
- Geopandas
- Rasterio
- Folium
- Matplotlib
- Psycopg2

---

## Usage
1. **Launch the Application**:
   Run the `main_code.py` script to start the GUI.
2. **Upload Data**:
   Use the `File` menu to upload raster or shapefile data.
3. **Perform Operations**:
   Select operations like calculating indices, clipping raster data, or buffering shapefiles from the menu.
4. **Visualize Results**:
   View data in the GUI or open an interactive map for shapefile visualizations.
5. **Export Data**:
   Save processed data to a local file for future use.

---

## Example Workflows
- **Calculate NDVI**:
  1. Upload a GeoTIFF file.
  2. Select "Calculate NDVI" from the menu.
  3. Input the band numbers for Red and NIR when prompted.
  4. View the result and export if needed.

- **Clip Raster**:
  1. Upload both a raster and a shapefile.
  2. Select "Clip Raster" from the menu.
  3. View the clipped output and export it.

---

## Troubleshooting
- **Error Loading Data**:
  Ensure your files are valid GeoTIFF or shapefile formats with correct CRS.
- **Database Issues**:
  Verify that PostgreSQL/PostGIS is running and the connection parameters are correct.

---

## Contributing
Contributions, bug reports, and feature requests are welcome. Please create an issue or a pull request on this repository.

---

## License
This project is public and acredidted use is welcomed

--- 