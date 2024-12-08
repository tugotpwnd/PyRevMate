import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from adjustText import adjust_text

class VisualizationWindow(QMainWindow):
    def __init__(self, data):
        """
        Initialize the visualization window.

        Parameters:
        - data: List of dictionaries containing raw data with keys like "Tag" and "Position".
        """
        super().__init__()
        self.setWindowTitle("Field Visualization")
        self.setGeometry(100, 100, 800, 600)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create matplotlib figure and canvas
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Add matplotlib's built-in toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)

        # Process raw data for visualization
        self.processed_data = self._process_data(data)

        # Plot processed data
        self.plot_data(self.processed_data)

    def _process_data(self, data):
        """
        Process raw data to extract necessary fields for visualization.

        Parameters:
        - data: Raw data to be processed.

        Returns:
        - List of dictionaries containing "Tag" and (X, Y) position pairs.
        """
        processed_data = []

        try:
            for item in data:
                # Check if required keys are in the item
                if "Tag" not in item or "Position" not in item:
                    print(f"ERROR: Missing keys in item: {item}")
                    continue

                # Check if Position is a dictionary with "X" and "Y" keys
                if not isinstance(item["Position"], dict) or "X" not in item["Position"] or "Y" not in item["Position"]:
                    print(f"ERROR: Invalid Position format in item: {item}")
                    continue

                # Extract X and Y coordinates
                x = item["Position"]["X"]
                y = item["Position"]["Y"]

                # Add to processed data
                processed_data.append({
                    "Tag": item["Tag"],
                    "Position": (x, y)  # Store as a tuple for consistency
                })

        except Exception as e:
            print(f"ERROR: Exception occurred during data processing: {e}")
            raise

        return processed_data

    def plot_data(self, data):
        """Plot the field names on an X-Y plane with smaller text and fixed offsets."""
        self.ax.clear()  # Clear previous plots

        for i, item in enumerate(data):
            x, y = item["Position"]
            tag = item["Tag"]

            # Plot the position as a scatter point
            self.ax.scatter(x, y, color="blue", s=20)  # Mark the position

            # Add text with a fixed offset, alternating between above and below
            offset = 1 if i % 2 == 0 else -1  # Alternate offset direction
            self.ax.text(
                x, y + offset, tag,
                fontsize=6,  # Smaller text
                ha="center", va="center"  # Center-align text horizontally
            )

        # Set axis labels and title
        self.ax.set_title("Field Visualization", fontsize=14)
        self.ax.set_xlabel("X Coordinate", fontsize=12)
        self.ax.set_ylabel("Y Coordinate", fontsize=12)

        # Turn off the grid for a cleaner look
        self.ax.grid(False)

        # Adjust scaling to prevent points from being too close to the edges
        self.ax.margins(0.1)

        # Redraw the canvas
        self.canvas.draw()

