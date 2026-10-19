import threading
import time
import logging
from typing import Callable, Dict

logger = logging.getLogger(__name__)

def crc16(data: bytes) -> int:
    """
    Computes CRC-16 (Modbus) over the given data.
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc

def validate_frame(frame: bytes) -> bool:
    """
    Validates a radar UART frame using CRC-16.
    Assuming the last 2 bytes are the CRC (little-endian).
    """
    if len(frame) < 4:
        return False

    payload = frame[:-2]
    expected_crc = crc16(payload)
    actual_crc = int.from_bytes(frame[-2:], byteorder='little')

    return expected_crc == actual_crc

class SystemWatchdog:
    def __init__(self, timeout_ms: int = 500):
        self.timeout = timeout_ms / 1000.0
        self.components: Dict[str, float] = {}
        self.reconnect_callbacks: Dict[str, Callable] = {}
        self.running = False
        self.thread = None
        self.lock = threading.Lock()

    def register_component(self, name: str, reconnect_cb: Callable):
        with self.lock:
            self.components[name] = time.time()
            self.reconnect_callbacks[name] = reconnect_cb

    def ping(self, name: str):
        with self.lock:
            if name in self.components:
                self.components[name] = time.time()

    def _watch_loop(self):
        while self.running:
            now = time.time()
            with self.lock:
                for name, last_ping in self.components.items():
                    if now - last_ping > self.timeout:
                        logger.warning(f"Watchdog timeout on {name}. Attempting reconnect...")
                        # Reset ping to avoid continuous reconnection loops
                        self.components[name] = now

                        # Trigger reconnect callback in a new thread to avoid blocking watchdog
                        cb = self.reconnect_callbacks.get(name)
                        if cb:
                            threading.Thread(target=cb, daemon=True).start()

            time.sleep(self.timeout / 2.0)

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._watch_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

class FailSafeManager:
    def __init__(self):
        self.mode = "NOMINAL"

    def report_failure(self, component: str):
        logger.error(f"Component failure reported: {component}")
        if component == "front_left_radar" or component == "front_right_radar":
            self.mode = "MONOCULAR_RADAR"
            logger.info("Degrading mode to MONOCULAR_RADAR. Error margins widened to +/- 20cm.")
        elif component == "optical":
            self.mode = "PURE_RADAR_TACTICAL"
            logger.info("Degrading mode to PURE_RADAR_TACTICAL.")

    def report_recovery(self, component: str):
        logger.info(f"Component recovered: {component}")
        self.mode = "NOMINAL"
