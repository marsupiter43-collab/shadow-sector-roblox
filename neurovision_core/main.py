import yaml
import queue
import threading
import time
import asyncio
import numpy as np
import logging
import sys

from core.radar_parser import AsyncSerialReader, RadarTarget
from core.triangulation import StereoTriangulator, Point2D
from core.kalman_tracker import TargetManager
from core.projection import CameraProjector
from core.safety import SystemWatchdog, FailSafeManager
from core.vision_engine import VisionEngine, SensorFusionEngine
from gui.gui_overlay import launch_gui

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NeuroVisionCore:
    def __init__(self, config_path: str = 'config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.radar_queue_l = asyncio.Queue(maxsize=10)
        self.radar_queue_r = asyncio.Queue(maxsize=10)

        # Threads bridging queue
        self.radar_fused_queue = queue.Queue(maxsize=1)
        self.gui_data_queue = queue.Queue(maxsize=1)

        self.running = False

        # Modules
        self.triangulator = StereoTriangulator(baseline_mm=150.0)
        self.target_manager = TargetManager()
        self.projector = CameraProjector(self.config['hardware']['cameras']['front']['intrinsic_k'])
        self.watchdog = SystemWatchdog()
        self.failsafe = FailSafeManager()

        self.vision_engine = VisionEngine(
            camera_index=self.config['hardware']['cameras']['front']['index'],
            model_path=self.config['algorithm']['yolo']['model']
        )
        self.fusion_engine = SensorFusionEngine()

        self.loop = None
        self.sys_fps = 0.0

    async def _async_radar_loop(self):
        # We start serial readers here
        port_l = self.config['hardware']['radars']['front_left']['port']
        baud_l = self.config['hardware']['radars']['front_left']['baudrate']
        port_r = self.config['hardware']['radars']['front_right']['port']
        baud_r = self.config['hardware']['radars']['front_right']['baudrate']

        reader_l = AsyncSerialReader(port_l, baud_l)
        reader_r = AsyncSerialReader(port_r, baud_r)

        try:
            await asyncio.gather(
                reader_l.connect(),
                reader_r.connect()
            )
        except Exception as e:
            logger.error(f"Failed to connect to radars: {e}")
            self.failsafe.report_failure("front_left_radar")

        # Start read loops
        asyncio.create_task(reader_l.read_loop(self.radar_queue_l))
        asyncio.create_task(reader_r.read_loop(self.radar_queue_r))

        while self.running:
            # Gather targets over a small time window
            targets_l = []
            targets_r = []

            try:
                while not self.radar_queue_l.empty():
                    targets = self.radar_queue_l.get_nowait()
                    targets_l.extend([Point2D(t.x, t.y) for t in targets])
            except asyncio.QueueEmpty:
                pass

            try:
                while not self.radar_queue_r.empty():
                    targets = self.radar_queue_r.get_nowait()
                    targets_r.extend([Point2D(t.x, t.y) for t in targets])
            except asyncio.QueueEmpty:
                pass

            if targets_l or targets_r:
                triangulated = self.triangulator.triangulate(targets_l, targets_r)

                # Format for target manager
                measurements = [np.array([t.x, t.y]) for t in triangulated]

                # We should ping watchdog
                self.watchdog.ping("front_left_radar")

                # Process in Target Manager
                self.target_manager.process_measurements(measurements)

                # Extract tracked states
                tracked_targets = []
                for tid, tracker in self.target_manager.trackers.items():
                    x = float(tracker.x[0,0])
                    y = float(tracker.x[1,0])
                    vx = float(tracker.x[2,0])
                    vy = float(tracker.x[3,0])

                    # Generate 3D wireframe
                    wireframe = self.projector.generate_3d_bbox(x, y, vx, vy)

                    tracked_targets.append({
                        'id': tid,
                        'x': x,
                        'y': y,
                        'vx': vx,
                        'vy': vy,
                        'wireframe': wireframe
                    })

                if not self.radar_fused_queue.full():
                    try:
                        self.radar_fused_queue.put_nowait(tracked_targets)
                    except queue.Full:
                        pass

            await asyncio.sleep(0.033)

    def _radar_thread_runner(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._async_radar_loop())

    def _main_fusion_loop(self):
        last_time = time.time()
        frames = 0
        fps_update_time = time.time()

        while self.running:
            loop_start = time.time()

            # Get latest vision data
            frame = None
            detections = []
            try:
                frame, detections = self.vision_engine.detection_queue.get(timeout=0.01)
                self.watchdog.ping("optical")
            except queue.Empty:
                pass

            # Get latest radar data
            radar_targets = []
            try:
                # We might not get radar every vision frame, keep last known if needed, but for now just poll
                radar_targets = self.radar_fused_queue.get_nowait()
            except queue.Empty:
                pass

            if frame is not None:
                # Fuse
                fused = self.fusion_engine.fuse(radar_targets, detections, lambda x,y,z: self.projector.project_point(x,y,z))

                # Calculate metrics
                frames += 1
                now = time.time()
                if now - fps_update_time >= 1.0:
                    self.sys_fps = frames / (now - fps_update_time)
                    frames = 0
                    fps_update_time = now

                latency = (time.time() - loop_start) * 1000.0

                telemetry = {
                    'fps': self.sys_fps,
                    'latency': latency,
                    'mode': self.failsafe.mode
                }

                # Send to GUI
                if self.gui_data_queue.full():
                    try:
                        self.gui_data_queue.get_nowait()
                    except queue.Empty:
                        pass
                self.gui_data_queue.put_nowait((frame, fused, telemetry))

    def start(self):
        self.running = True

        # Start Watchdog
        self.watchdog.register_component("front_left_radar", lambda: None)
        self.watchdog.register_component("optical", lambda: None)
        self.watchdog.start()

        # Start Vision
        self.vision_engine.start()

        # Start Radar Thread
        self.radar_thread = threading.Thread(target=self._radar_thread_runner, daemon=True)
        self.radar_thread.start()

        # Start Fusion Thread
        self.fusion_thread = threading.Thread(target=self._main_fusion_loop, daemon=True)
        self.fusion_thread.start()

        # Launch GUI (blocking in main thread)
        launch_gui(self.gui_data_queue)

    def stop(self):
        self.running = False
        self.vision_engine.stop()
        self.watchdog.stop()
        if self.loop:
            self.loop.stop()

if __name__ == "__main__":
    core = NeuroVisionCore()
    try:
        core.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        core.stop()
