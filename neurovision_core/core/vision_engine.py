import cv2
import threading
import queue
import time
import logging
from ultralytics import YOLO
import numpy as np

logger = logging.getLogger(__name__)

class VisionEngine:
    def __init__(self, camera_index: int, model_path: str, width: int = 1920, height: int = 1080):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.cap = None
        self.running = False
        self.frame_queue = queue.Queue(maxsize=1)
        self.detection_queue = queue.Queue(maxsize=1)

        # Load model. Assuming YOLOv8
        try:
            # Note: To use TensorRT/CUDA, device='0' and half=True would be set here.
            # We initialize standard, then use .to('cuda') if available.
            self.model = YOLO(model_path)
            # Will automatically use GPU if torch is compiled with CUDA
            logger.info(f"Loaded YOLO model from {model_path}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.model = None

    def start(self):
        # Open with CAP_DSHOW to eliminate buffer lag on Windows
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, 60)

        if not self.cap.isOpened():
            logger.error(f"Failed to open camera {self.camera_index}")
            return

        self.running = True

        # Start capture thread
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()

        # Start inference thread
        self.inference_thread = threading.Thread(target=self._inference_loop, daemon=True)
        self.inference_thread.start()

    def _capture_loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                # Keep only the latest frame
                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()
                    except queue.Empty:
                        pass
                self.frame_queue.put_nowait(frame)
            else:
                time.sleep(0.01)

    def _inference_loop(self):
        while self.running:
            try:
                frame = self.frame_queue.get(timeout=0.1)

                if self.model:
                    # Run inference. half=True for FP16, device=0 for CUDA (assumes CUDA is available)
                    # For cross-platform robust testing, we rely on ultralytics default device selection
                    results = self.model(frame, verbose=False, classes=[0], conf=0.5) # Class 0 = person

                    detections = []
                    for r in results:
                        boxes = r.boxes
                        for box in boxes:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            conf = float(box.conf[0].cpu().numpy())
                            cls = int(box.cls[0].cpu().numpy())
                            detections.append({
                                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                                'conf': conf,
                                'class': cls
                            })

                    if self.detection_queue.full():
                        try:
                            self.detection_queue.get_nowait()
                        except queue.Empty:
                            pass
                    self.detection_queue.put_nowait((frame, detections))
                else:
                    # If model didn't load, just pass the frame
                    if self.detection_queue.full():
                        try:
                            self.detection_queue.get_nowait()
                        except queue.Empty:
                            pass
                    self.detection_queue.put_nowait((frame, []))

            except queue.Empty:
                pass

    def stop(self):
        self.running = False
        if hasattr(self, 'capture_thread'):
            self.capture_thread.join()
        if hasattr(self, 'inference_thread'):
            self.inference_thread.join()
        if self.cap:
            self.cap.release()

class SensorFusionEngine:
    def __init__(self):
        pass

    def fuse(self, radar_targets: list, optical_detections: list, projection_func):
        """
        Fuses radar tracks with optical bounding boxes.
        Returns a list of final unified targets to render.
        """
        fused_targets = []

        # Simple fusion: For each radar target, project to 2D and check overlap with optical
        for rt in radar_targets:
            # rt is expected to be a tracked target with x, y, vx, vy
            # Project to center of bounding box expected
            proj = projection_func(rt['x'], rt['y'], 0.0) # Assume chest height Z=0 relative to radar

            is_visible = False
            best_bbox = None

            if proj:
                px, py = proj

                # Check optical overlap
                for opt in optical_detections:
                    bx1, by1, bx2, by2 = opt['bbox']
                    # Increase bounding box slightly for tolerance
                    pad = 50
                    if bx1 - pad <= px <= bx2 + pad and by1 - pad <= py <= by2 + pad:
                        is_visible = True
                        best_bbox = opt['bbox']
                        break

            # Determine rendering strategy and IFF
            # Basic IFF logic placeholder
            iff = "NEUTRAL"

            fused_targets.append({
                'radar_data': rt,
                'is_visible': is_visible,
                'optical_bbox': best_bbox,
                'iff': iff
            })

        return fused_targets
