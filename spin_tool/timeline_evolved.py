import sys
import json
from collections import defaultdict

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QScrollArea, QWidget,
    QVBoxLayout
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class TimelineCanvas(FigureCanvas):
    def __init__(self, trail_data):
        self.fig = Figure(figsize=(30, 6))  # Wide initial figure for scrolling
        super().__init__(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.trail_data = trail_data
        self.draw_timeline()

    def draw_timeline(self):
        self.ax.clear()

        process_timelines = defaultdict(list)
        for entry in self.trail_data:
            process_timelines[entry["proc_name"]].append((entry["step"], entry["line"], entry["action"]))

        processes = list(process_timelines.keys())
        colors = plt.cm.get_cmap("tab10", len(processes))

        for i, proc in enumerate(processes):
            timeline = process_timelines[proc]
            y = i
            for step, line, action in timeline:
                self.ax.broken_barh([(step, 1)], (y - 0.4, 0.8), facecolors=colors(i), edgecolor="black")
                if len(timeline) < 100:
                    self.ax.text(step + 0.1, y, f"L{line}", va="center", ha="left", fontsize=7)

        self.ax.set_yticks(range(len(processes)))
        self.ax.set_yticklabels(processes)
        self.ax.set_xlabel("Step")
        self.ax.set_title("Process Execution Timeline")
        self.ax.grid(True, axis="x", linestyle="--", alpha=0.5)

        self.fig.tight_layout()
        self.draw()


class TimelineViewer(QMainWindow):
    def __init__(self, trail_data):
        super().__init__()
        self.setWindowTitle("SPIN Process Timeline Viewer")
        self.resize(1000, 600)

        main_widget = QWidget()
        main_layout = QVBoxLayout()


        canvas_container = QWidget()
        canvas_layout = QVBoxLayout()
        self.canvas = TimelineCanvas(trail_data)
        self.canvas.setMinimumWidth(2000)  
        canvas_layout.addWidget(self.canvas)
        canvas_container.setLayout(canvas_layout)

        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(canvas_container)

        main_layout.addWidget(scroll_area)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)


def load_trail_from_file(path: str):
    with open(path, "r") as f:
        data = json.load(f)
    return data["trail"]


if __name__ == "__main__":
    app = QApplication(sys.argv)

    try:
        trail_data = load_trail_from_file("output/parsed_data.json")
        viewer = TimelineViewer(trail_data)
        viewer.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error: {e}")
