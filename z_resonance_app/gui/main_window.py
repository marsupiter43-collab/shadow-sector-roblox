import sys
import numpy as np
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QComboBox, QGroupBox, QGridLayout)
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor
import pyqtgraph as pg

from z_resonance_app.engine.grid import TissueGrid
from z_resonance_app.engine.fdtd import FDTDSolver
from z_resonance_app.engine.optimizer import PhaseOptimizer
from .styles import MEDICAL_DARK_THEME

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Z-RESONANCE Medical Simulator")
        self.resize(1200, 800)
        self.setStyleSheet(MEDICAL_DARK_THEME)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        self.setup_control_panel()
        self.setup_display_panel()

        self.timer = QTimer()
        self.timer.timeout.connect(self.simulation_step)

        self.is_running = False
        self.time_step = 0

        self.init_simulation()

    def setup_control_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        panel.setFixedWidth(300)

        title = QLabel("Z-RESONANCE\nControl Panel")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        # Settings
        settings_group = QGroupBox("Simulation Parameters")
        settings_layout = QVBoxLayout()

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["Homogeneous Tissue", "Deep Target behind Dense Bone Barrier"])
        self.preset_combo.currentIndexChanged.connect(self.reset_simulation)
        settings_layout.addWidget(QLabel("Anatomical Preset:"))
        settings_layout.addWidget(self.preset_combo)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Mode A: Standard Transmission", "Mode B: Z-Resonance Phase-Matched"])
        self.mode_combo.currentIndexChanged.connect(self.reset_simulation)
        settings_layout.addWidget(QLabel("Operation Mode:"))
        settings_layout.addWidget(self.mode_combo)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Controls
        controls_group = QGroupBox("Execution")
        controls_layout = QGridLayout()

        self.btn_run = QPushButton("RUN")
        self.btn_run.setObjectName("runButton")
        self.btn_run.clicked.connect(self.toggle_simulation)

        self.btn_reset = QPushButton("RESET")
        self.btn_reset.clicked.connect(self.reset_simulation)

        controls_layout.addWidget(self.btn_run, 0, 0)
        controls_layout.addWidget(self.btn_reset, 0, 1)

        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        # Telemetry
        self.telemetry_label = QLabel("Status: Idle\nFPS: 0\nMax E-Field: 0.00e+00")
        layout.addWidget(self.telemetry_label)

        layout.addStretch()
        self.main_layout.addWidget(panel)

    def setup_display_panel(self):
        display_layout = QVBoxLayout()

        # Viewport
        self.plot_widget = pg.PlotWidget(title="Real-Time 2D Wave Propagation")
        self.img = pg.ImageItem()
        self.plot_widget.addItem(self.img)

        # Colormap
        colormap = pg.colormap.get('viridis')
        self.img.setLookupTable(colormap.getLookupTable())

        # Target crosshair
        self.v_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('r', width=1, style=pg.QtCore.Qt.PenStyle.DashLine))
        self.h_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('r', width=1, style=pg.QtCore.Qt.PenStyle.DashLine))
        self.plot_widget.addItem(self.v_line)
        self.plot_widget.addItem(self.h_line)

        display_layout.addWidget(self.plot_widget, stretch=3)

        # Telemetry Plot
        self.telemetry_plot = pg.PlotWidget(title="Energy Density: Target vs Healthy Tissue")
        self.telemetry_plot.addLegend()
        self.target_curve = self.telemetry_plot.plot(pen='r', name="Target Energy")
        self.healthy_curve = self.telemetry_plot.plot(pen='g', name="Max Healthy Energy")
        self.target_data = []
        self.healthy_data = []

        display_layout.addWidget(self.telemetry_plot, stretch=1)

        self.main_layout.addLayout(display_layout)

    def init_simulation(self):
        # Default grid 200x200, 1mm resolution
        self.grid = TissueGrid(nx=200, ny=200, dx=1e-3, dy=1e-3)
        self.grid.apply_preset(self.preset_combo.currentText())

        # Crosshair update
        tx, ty = self.grid.target_coord
        self.v_line.setPos(tx)
        self.h_line.setPos(ty)

        # DT slightly below CFL
        c_max = 299792458.0 / np.sqrt(self.grid.EPSILON_MIN)
        dt_cfl = 1.0 / (c_max * np.sqrt((1.0 / self.grid.dx**2) + (1.0 / self.grid.dy**2)))
        self.dt = dt_cfl * 0.95

        self.solver = FDTDSolver(grid=self.grid, dt=self.dt)
        self.optimizer = PhaseOptimizer(solver=self.solver)

        self.frequency = 1e9 # 1 GHz ultrasound / microwave equivalent

        if self.mode_combo.currentIndex() == 1:
            self.delays = self.optimizer.calculate_phase_delays(self.frequency)
        else:
            self.delays = None

        self.time_step = 0
        self.target_data.clear()
        self.healthy_data.clear()
        self.update_display()

    def toggle_simulation(self):
        self.is_running = not self.is_running
        if self.is_running:
            self.btn_run.setText("PAUSE")
            self.btn_run.setObjectName("stopButton")
            # Force style reload for dynamic ID change
            self.btn_run.setStyleSheet(self.btn_run.styleSheet())
            self.timer.start(10) # 10ms timer
        else:
            self.btn_run.setText("RUN")
            self.btn_run.setObjectName("runButton")
            self.btn_run.setStyleSheet(self.btn_run.styleSheet())
            self.timer.stop()
            self.telemetry_label.setText(f"Status: Paused\nFPS: 0\nMax E-Field: {self.max_e:.2e}")

    def reset_simulation(self):
        if self.is_running:
            self.toggle_simulation()
        self.init_simulation()
        self.telemetry_label.setText("Status: Reset\nFPS: 0\nMax E-Field: 0.00e+00")

    def simulation_step(self):
        # Run multiple FDTD steps per GUI update for speed
        steps_per_frame = 10
        try:
            for _ in range(steps_per_frame):
                self.solver.step()
                if self.mode_combo.currentIndex() == 0:
                    max_e = self.optimizer.emit_standard(self.time_step, self.frequency)
                else:
                    max_e = self.optimizer.emit_phase_matched(self.time_step, self.frequency, self.delays)
                self.time_step += 1

            self.max_e = max_e
            self.update_display()
            self.telemetry_label.setText(f"Status: Running\nTime Step: {self.time_step}\nMax E-Field: {self.max_e:.2e}")

        except Exception as e:
            self.toggle_simulation()
            self.telemetry_label.setText(f"Status: ERROR/CUTOFF\n{str(e)}")

    def update_display(self):
        # Update 2D field
        field_data = self.solver.Ez.cpu().numpy()
        # Overlay tissue structure lightly
        tissue_display = self.grid.epsilon_r / self.grid.EPSILON_MAX * 0.1
        display_data = np.abs(field_data) + tissue_display
        self.img.setImage(display_data, autoLevels=True)

        # Update Telemetry Plot
        tx, ty = self.grid.target_coord
        target_energy = (field_data[tx, ty])**2
        healthy_field_data = field_data[self.optimizer.healthy_mask.cpu().numpy()]
        healthy_energy = np.max(healthy_field_data**2) if len(healthy_field_data) > 0 else 0

        self.target_data.append(target_energy)
        self.healthy_data.append(healthy_energy)

        # Keep last 100 points
        if len(self.target_data) > 100:
            self.target_data.pop(0)
            self.healthy_data.pop(0)

        self.target_curve.setData(self.target_data)
        self.healthy_curve.setData(self.healthy_data)
