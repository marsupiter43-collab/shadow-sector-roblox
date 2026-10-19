import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_imports():
    from core.radar_parser import HLKLD2450Parser, AsyncSerialReader
    from core.triangulation import StereoTriangulator, Point2D
    from core.kalman_tracker import EKFTracker, TargetManager
    from core.projection import CameraProjector
    from core.safety import SystemWatchdog, FailSafeManager
    from core.vision_engine import VisionEngine, SensorFusionEngine
    from gui.gui_overlay import launch_gui
    from main import NeuroVisionCore

    assert True
