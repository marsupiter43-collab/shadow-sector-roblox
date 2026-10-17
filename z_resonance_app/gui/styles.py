MEDICAL_DARK_THEME = """
QMainWindow {
    background-color: #0b0f19;
    color: #e0e6ed;
}

QWidget {
    background-color: #0b0f19;
    color: #e0e6ed;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QGroupBox {
    border: 1px solid #1f2937;
    border-radius: 4px;
    margin-top: 1ex;
    font-weight: bold;
    color: #38bdf8;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px 0 3px;
}

QPushButton {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 4px;
    color: #f8fafc;
    padding: 5px 15px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #334155;
    border: 1px solid #475569;
}

QPushButton:pressed {
    background-color: #0f172a;
}

QPushButton#runButton {
    background-color: #166534;
    border-color: #14532d;
}

QPushButton#runButton:hover {
    background-color: #15803d;
}

QPushButton#stopButton {
    background-color: #991b1b;
    border-color: #7f1d1d;
}

QPushButton#stopButton:hover {
    background-color: #b91c1c;
}

QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 4px;
    color: #f8fafc;
    padding: 2px 5px;
}

QComboBox::drop-down {
    border: 0px;
}

QLabel {
    color: #94a3b8;
}

QLabel#titleLabel {
    color: #38bdf8;
    font-size: 18px;
    font-weight: bold;
    padding: 10px;
}
"""
