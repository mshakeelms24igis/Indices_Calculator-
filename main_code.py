import sys  # Provides system-specific parameters and functions
from PyQt5.QtWidgets import (  # Import PyQt5 modules for building the GUI
    QApplication, QMainWindow, QAction, QVBoxLayout, QWidget,
    QFileDialog, QLabel, QMessageBox, QInputDialog, QLineEdit, QTabWidget
)
from PyQt5.QtCore import Qt  # Qt constants and core functionalities
from PyQt5.QtGui import QPalette, QColor  # GUI color and palette settings
import rasterio  # Library for handling raster data
from rasterio.mask import mask  # Function for masking raster data using vector geometries
import geopandas as gpd  # Library for geospatial data manipulation
import numpy as np  # Numerical computation library
import folium  # For creating interactive maps
import os  # Operating system interface for file and path handling
import webbrowser  # Allows interaction with the web browser
import psycopg2  # PostgreSQL database connection library
import matplotlib.pyplot as plt  # Visualization library
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas  # Embeds matplotlib in PyQt5

# Helper Functions
def calculate_ndvi(red, nir):  # Function to calculate NDVI index
    red = red.astype(float)  # Convert red band to float
    nir = nir.astype(float)  # Convert NIR band to float
    return np.where((nir + red) == 0, 0, (nir - red) / (nir + red))  # NDVI formula

def calculate_ndwi(green, nir):  # Function to calculate NDWI index (corrected)
    green = green.astype(float)  # Convert green band to float
    nir = nir.astype(float)  # Convert NIR band to float
    return np.where((green + nir) == 0, 0, (green - nir) / (green + nir))  # Corrected NDWI formula

def calculate_ndbi(swir, nir):  # Function to calculate NDBI index
    swir = swir.astype(float)  # Convert SWIR band to float
    nir = nir.astype(float)  # Convert NIR band to float
    return np.where((swir + nir) == 0, 0, (swir - nir) / (swir + nir))  # NDBI formula

class MainWindow(QMainWindow):  # Main application window class
    def __init__(self):  # Constructor
        super().__init__()  # Initialize the parent class
        self.setWindowTitle("Spectral Indices Calculator")  # Set window title
        self.setGeometry(100, 100, 1200, 800)  # Set the dimensions of the main window

        # Initialize variables
        self.raster_path = None  # Path to the uploaded raster file
        self.shapefile_path = None  # Path to the uploaded shapefile
        self.raster_data = None  # Loaded raster data object
        self.gdf = None  # GeoDataFrame for shapefiles
        self.db_connection = None  # Connection object for PostgreSQL
        self.last_displayed_data = None  # Stores the most recent visualization data
        self.last_displayed_type = None  # Type of data visualized (e.g., raster, shapefile)

        # Set up colors and styling
        self.setStyleSheet("background-color: #e8f4f8;")  # Set background color for the application
        palette = QPalette()  # Initialize a color palette
        palette.setColor(QPalette.Window, QColor("#e8f4f8"))  # Set the window background color
        palette.setColor(QPalette.WindowText, QColor("#2c3e50"))  # Set the text color
        palette.setColor(QPalette.Text, QColor("#2c3e50"))  # Set input text color
        self.setPalette(palette)  # Apply the palette

        self.central_widget = QTabWidget()  # Create a tabbed widget for managing multiple views
        self.setCentralWidget(self.central_widget)  # Set it as the central widget
        self.setup_menu()  # Setup the menu bar

    def setup_menu(self):  # Function to create the menu bar
        menubar = self.menuBar()  # Initialize the menu bar
        menubar.setStyleSheet(  # Styling for the menu bar
            "background-color: #3498db; color: white; font-size: 16px;"
            "QMenu::item:selected { background-color: red; color: white; }"
        )

        # File menu
        file_menu = menubar.addMenu("File")  # Add a "File" menu
        file_menu.addAction(self.create_action("Upload Raster", self.upload_raster))  # Action for uploading raster
        file_menu.addAction(self.create_action("Upload Shapefile", self.upload_shapefile))  # Action for shapefile

        # Add menus for indices calculations
        ndvi_menu = menubar.addMenu("Calculate NDVI")
        ndvi_menu.addAction(self.create_action("NDVI", lambda: self.calculate_index("NDVI")))

        ndbi_menu = menubar.addMenu("Calculate NDBI")
        ndbi_menu.addAction(self.create_action("NDBI", lambda: self.calculate_index("NDBI")))

        ndwi_menu = menubar.addMenu("Calculate NDWI")
        ndwi_menu.addAction(self.create_action("NDWI", lambda: self.calculate_index("NDWI")))

        # Other menus for operations
        buffer_tool_menu = menubar.addMenu("Buffer Tool")
        buffer_tool_menu.addAction(self.create_action("Buffer Tool", self.buffer_tool))

        clip_raster_menu = menubar.addMenu("Clip Raster")
        clip_raster_menu.addAction(self.create_action("Clip Raster", self.clip_raster))

        visualization_raster_menu = menubar.addMenu("Visualize Raster")
        visualization_raster_menu.addAction(self.create_action("Display Raster", self.display_raster))

        visualization_vector_menu = menubar.addMenu("Visualize Vector")
        visualization_vector_menu.addAction(self.create_action("Visualize Shapefile (Map)", self.visualize_shapefile))
        visualization_vector_menu.addAction(self.create_action("Visualize Shapefile (GUI)", self.visualize_shapefile_on_gui))

        export_menu = menubar.addMenu("Export")
        export_menu.addAction(self.create_action("Export Displayed Data", self.export_displayed_data))

        db_menu = menubar.addMenu("Database")
        db_menu.addAction(self.create_action("Connect to PostGIS", self.connect_to_postgis))
        db_menu.addAction(self.create_action("Import and Visualize from PostGIS", self.import_and_visualize_from_postgis))

    def create_action(self, text, slot):  # Helper to create an action for the menu
        action = QAction(text, self)  # Create a new QAction
        action.triggered.connect(slot)  # Connect the action to the slot (function)
        return action

    def add_tab(self, widget, title):  # Add a new tab to the central widget
        self.central_widget.addTab(widget, title)
        self.central_widget.setCurrentWidget(widget)

    def upload_raster(self):  # Function to handle raster file upload
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Raster File", "", "GeoTIFF files (*.tif);;All Files (*)")
        if file_name:  # Check if a file is selected
            try:
                self.raster_data = rasterio.open(file_name)  # Open the raster file
                self.raster_path = file_name  # Save the file path
                QMessageBox.information(self, "Success", "Raster uploaded successfully!")  # Show success message
            except rasterio.errors.RasterioIOError:  # Handle invalid file errors
                QMessageBox.critical(self, "Error", "Invalid raster file.")

    def upload_shapefile(self):  # Function to handle shapefile upload
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Shapefile", "", "Shapefiles (*.shp);;All Files (*)")
        if file_name:  # Check if a file is selected
            try:
                self.gdf = gpd.read_file(file_name)  # Load shapefile as GeoDataFrame
                self.shapefile_path = file_name  # Save the file path
                QMessageBox.information(self, "Success", "Shapefile uploaded successfully!")  # Show success message
            except Exception as e:  # Handle file read errors
                QMessageBox.critical(self, "Error", f"Error loading shapefile: {e}")
    
    def buffer_tool(self):  # Function to create a buffer around a shapefile
        if not hasattr(self, 'gdf') or self.gdf.empty:  # Check if shapefile is uploaded
            QMessageBox.critical(self, "Error", "Please upload a shapefile first.")
            return
    
        try:
            distance, ok = QInputDialog.getDouble(self, "Buffer Distance", "Enter buffer distance (in map units):")
            if not ok or distance <= 0:
                QMessageBox.critical(self, "Error", "Invalid buffer distance.")
                return
    
            buffered_gdf = self.gdf.copy()
            buffered_gdf['geometry'] = buffered_gdf.geometry.buffer(distance)
    
            self.last_displayed_data = buffered_gdf  # Store the buffered shapefile
            self.last_displayed_type = "shapefile"  # Set data type to shapefile
    
            fig, ax = plt.subplots()
            buffered_gdf.plot(ax=ax)
            plt.show()
    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")
            print(f"An error occurred: {e}")  # Print the error to the console for debugging
    def clip_raster(self):  # Function to clip the raster using a shapefile
        if not self.raster_data or not self.gdf:  # Check if both files are uploaded
            QMessageBox.critical(self, "Error", "Please upload raster and shapefile first.")
            return

        try:
            if self.gdf.crs != self.raster_data.crs:  # Ensure the CRS matches
                self.gdf = self.gdf.to_crs(self.raster_data.crs)

            shapes = [geom for geom in self.gdf.geometry if geom.is_valid]  # Extract valid geometries
            out_image, out_transform = mask(self.raster_data, shapes, crop=True)  # Perform the clipping

            self.last_displayed_data = out_image[0]  # Store the clipped raster
            self.last_displayed_type = "raster"  # Set data type to raster

            self.show_image(out_image[0], "Clipped Raster")  # Display the clipped raster

            QMessageBox.information(self, "Success", "Raster clipped successfully!")  # Show success message
        except Exception as e:  # Handle errors
            QMessageBox.critical(self, "Error", f"Error while clipping raster: {e}")

    def calculate_index(self, index_type):  # Function to calculate spectral indices
        if not self.raster_data:  # Check if raster file is uploaded
            QMessageBox.critical(self, "Error", "Please upload a raster first.")
            return

        try:
            red_band, _ = QInputDialog.getInt(self, "Red Band", "Enter Red Band Number:")  # Get red band input
            nir_band, _ = QInputDialog.getInt(self, "NIR Band", "Enter NIR Band Number:")  # Get NIR band input
            green_band, _ = QInputDialog.getInt(self, "Green Band", "Enter Green Band Number:")  # Get green band input
            swir_band, _ = QInputDialog.getInt(self, "SWIR Band", "Enter SWIR Band Number:")  # Get SWIR band input

            if index_type == "NDVI":  # Calculate NDVI
                red = self.raster_data.read(red_band)
                nir = self.raster_data.read(nir_band)
                index_result = calculate_ndvi(red, nir)
            elif index_type == "NDWI":  # Calculate NDWI
                green = self.raster_data.read(green_band)
                nir = self.raster_data.read(nir_band)
                index_result = calculate_ndwi(green, nir)
            elif index_type == "NDBI":  # Calculate NDBI
                swir = self.raster_data.read(swir_band)
                nir = self.raster_data.read(nir_band)
                index_result = calculate_ndbi(swir, nir)

            self.last_displayed_data = index_result  # Store the calculated index
            self.last_displayed_type = "raster"  # Set data type to raster

            self.show_image(index_result, f"{index_type} Image")  # Display the index result
        except Exception as e:  # Handle errors during calculation
            QMessageBox.critical(self, "Error", f"Error calculating {index_type}: {e}")

    def display_raster(self):  # Function to display raster data
        if not self.raster_data:  # Check if raster is uploaded
            QMessageBox.critical(self, "Error", "No raster uploaded.")
            return
        try:
            band_index, ok = QInputDialog.getInt(self, "Select Band", "Enter Band Number to Display:")  # Get band input
            if not ok or band_index <= 0:  # Validate input
                QMessageBox.critical(self, "Error", "Invalid band number.")
                return
            raster_band = self.raster_data.read(band_index)  # Read the selected band

            self.last_displayed_data = raster_band  # Store raster band data
            self.last_displayed_type = "raster"  # Set data type to raster

            fig, ax = plt.subplots()  # Create a plot
            im = ax.imshow(raster_band, cmap='gray')  # Plot raster band
            fig.colorbar(im, ax=ax)  # Add colorbar to the plot
            ax.set_title(f"Raster Band {band_index}")  # Set plot title
            canvas = FigureCanvas(fig)  # Create canvas for the plot
            widget = QWidget()  # Create a QWidget to hold the canvas
            layout = QVBoxLayout()  # Create a vertical layout
            layout.addWidget(canvas)  # Add canvas to the layout
            widget.setLayout(layout)  # Set layout for the widget
            self.add_tab(widget, f"Raster Band {band_index}")  # Add the widget as a new tab
        except Exception as e:  # Handle errors
            QMessageBox.critical(self, "Error", f"Error displaying raster: {e}")

    def visualize_shapefile(self):  # Function to visualize shapefile as a map
        if not self.shapefile_path:  # Check if shapefile is uploaded
            QMessageBox.critical(self, "Error", "No shapefile uploaded.")
            return
        try:
            shapefile = gpd.read_file(self.shapefile_path)  # Load shapefile
            if shapefile.crs is None:  # Ensure CRS is set
                shapefile = shapefile.set_crs(epsg=4326)
            elif not shapefile.crs.is_geographic:
                shapefile = shapefile.to_crs(epsg=4326)

            shapefile = shapefile[shapefile.is_valid]  # Filter invalid geometries
            if shapefile.empty:
                QMessageBox.critical(self, "Error", "Shapefile contains no valid geometries.")
                return

            self.last_displayed_data = shapefile  # Store shapefile
            self.last_displayed_type = "shapefile"  # Set data type to shapefile

            centroid = shapefile.geometry.unary_union.centroid  # Calculate the centroid
            fmap = folium.Map(location=[centroid.y, centroid.x], zoom_start=12)  # Create Folium map
            folium.GeoJson(shapefile).add_to(fmap)  # Add shapefile as GeoJSON to map

            map_path = os.path.join(os.path.dirname(self.shapefile_path), "shapefile_map.html")  # Save path
            fmap.save(map_path)  # Save map as an HTML file
            webbrowser.open(map_path)  # Open the map in the browser
        except Exception as e:  # Handle errors
            QMessageBox.critical(self, "Error", f"Error visualizing shapefile: {e}")

    def visualize_shapefile_on_gui(self):  # Function to visualize shapefile on GUI
        if not self.shapefile_path:  # Check if shapefile is uploaded
            QMessageBox.critical(self, "Error", "No shapefile uploaded.")
            return
        try:
            shapefile = gpd.read_file(self.shapefile_path)  # Load shapefile
            fig, ax = plt.subplots()  # Create a plot
            shapefile.plot(ax=ax, color='blue', edgecolor='black')  # Plot shapefile
            ax.set_title("Shapefile Visualization")  # Set plot title

            self.last_displayed_data = shapefile  # Store shapefile
            self.last_displayed_type = "shapefile"  # Set data type to shapefile

            canvas = FigureCanvas(fig)  # Create canvas for the plot
            widget = QWidget()  # Create a QWidget to hold the canvas
            layout = QVBoxLayout()  # Create a vertical layout
            layout.addWidget(canvas)  # Add canvas to the layout
            widget.setLayout(layout)  # Set layout for the widget
            self.add_tab(widget, "Shapefile GUI")  # Add the widget as a new tab
        except Exception as e:  # Handle errors
            QMessageBox.critical(self, "Error", f"Error visualizing shapefile on GUI: {e}")

    def connect_to_postgis(self):  # Function to connect to a PostGIS database
        try:
            host, ok = QInputDialog.getText(self, "Host", "Enter Host:")
            dbname, ok = QInputDialog.getText(self, "Database Name", "Enter Database Name:")
            user, ok = QInputDialog.getText(self, "Username", "Enter Username:")
            password, ok = QInputDialog.getText(self, "Password", "Enter Password:", QLineEdit.Password)
            self.db_connection = psycopg2.connect(host=host, dbname=dbname, user=user, password=password)
            QMessageBox.information(self, "Success", "Connected to PostGIS database successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error connecting to database: {e}")

    def import_and_visualize_from_postgis(self):  # Function to import and visualize data from PostGIS
        if not self.db_connection:
            QMessageBox.critical(self, "Error", "Please connect to the PostGIS database first.")
            return
        try:
            table_name, ok = QInputDialog.getText(self, "Table Name", "Enter Table Name:")
            if not ok or not table_name:
                QMessageBox.critical(self, "Error", "Invalid table name.")
                return
            query = f"SELECT * FROM {table_name}"
            self.gdf = gpd.read_postgis(query, self.db_connection, geom_col="geom")
            if self.gdf.crs is None:
                self.gdf = self.gdf.set_crs(epsg=4326)
            centroid = self.gdf.geometry.centroid.iloc[0]
            fmap = folium.Map(location=[centroid.y, centroid.x], zoom_start=12)
            folium.GeoJson(self.gdf).add_to(fmap)

            output_path = os.path.expanduser("~/postgis_visualization.html")
            fmap.save(output_path)
            webbrowser.open(output_path)

            self.last_displayed_data = self.gdf
            self.last_displayed_type = "shapefile"
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error visualizing shapefile from PostGIS: {e}")

    def export_displayed_data(self):  # Function to export currently displayed data
        if self.last_displayed_data is None:
            QMessageBox.critical(self, "Error", "No data available to export.")
            return

        try:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "All Files (*)")
            if not file_path:
                QMessageBox.information(self, "Canceled", "Save operation canceled.")
                return

            if self.last_displayed_type == "shapefile":
                self.last_displayed_data.to_file(file_path, driver="ESRI Shapefile")
            elif self.last_displayed_type == "raster":
                with rasterio.open(
                    file_path,
                    "w",
                    driver="GTiff",
                    height=self.last_displayed_data.shape[0],
                    width=self.last_displayed_data.shape[1],
                    count=1,
                    dtype=self.last_displayed_data.dtype,
                    crs=self.raster_data.crs,
                    transform=self.raster_data.transform,
                ) as dst:
                    dst.write(self.last_displayed_data, 1)
            QMessageBox.information(self, "Success", f"Data exported successfully to {file_path}.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error exporting data: {e}")

    def show_image(self, image_data, title):  # Function to display an image
        fig, ax = plt.subplots()
        im = ax.imshow(image_data, cmap='viridis')
        fig.colorbar(im, ax=ax)
        ax.set_title(title)
        canvas = FigureCanvas(fig)
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(canvas)
        widget.setLayout(layout)
        self.add_tab(widget, title)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
