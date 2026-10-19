import asyncio
import struct
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RadarTarget:
    x: int # lateral mm
    y: int # distance mm
    speed: int # cm/s
    resolution: int # distance precision

class HLKLD2450Parser:
    def __init__(self):
        self.buffer = bytearray()
        self.HEADER = b'\xaa\xff\x03\x00'
        self.TAIL = b'\x55\xcc'

    def process_data(self, data: bytes) -> list[RadarTarget]:
        self.buffer.extend(data)
        targets = []

        while True:
            # Find header
            header_idx = self.buffer.find(self.HEADER)
            if header_idx == -1:
                # Keep last 3 bytes in case of partial header
                if len(self.buffer) > 3:
                    self.buffer = self.buffer[-3:]
                break

            # Remove anything before header
            if header_idx > 0:
                self.buffer = self.buffer[header_idx:]

            # Find tail
            tail_idx = self.buffer.find(self.TAIL)
            if tail_idx == -1:
                break # Wait for more data

            # Extract packet
            packet = self.buffer[:tail_idx + len(self.TAIL)]
            self.buffer = self.buffer[tail_idx + len(self.TAIL):]

            # Parse packet content. HLK-LD2450 typically sends 3 targets
            # packet format: header (4) + target1 (8) + target2 (8) + target3 (8) + tail (2)
            # But we'll just parse whatever we find.
            payload = packet[4:-2]

            # We assume each target is 8 bytes. x (16bit), y (16bit), speed (16bit), resolution (16bit)
            # Actually format is:
            # X coord (2 bytes, 15bit + 1 bit sign)
            # Y coord (2 bytes, 15bit + 1 bit sign) - wait usually Y is unsigned.
            # Speed (2 bytes, 15bit + 1 bit sign)
            # Resolution (2 bytes)

            target_size = 8
            for i in range(0, len(payload), target_size):
                if i + target_size <= len(payload):
                    target_data = payload[i:i+target_size]

                    x_raw, y_raw, speed_raw, resolution = struct.unpack('<HHHH', target_data)

                    # Process signs (highest bit indicates sign for HLK-LD2450)
                    x = x_raw & 0x7FFF
                    if x_raw & 0x8000:
                        x = -x

                    y = y_raw & 0x7FFF
                    if y_raw & 0x8000:
                        y = -y # Although y is usually positive

                    speed = speed_raw & 0x7FFF
                    if speed_raw & 0x8000:
                        speed = -speed

                    # Target 0,0,0 indicates no target
                    if x != 0 or y != 0:
                        targets.append(RadarTarget(x=x, y=y, speed=speed, resolution=resolution))

        return targets

class AsyncSerialReader:
    def __init__(self, port: str, baudrate: int):
        self.port = port
        self.baudrate = baudrate
        self.parser = HLKLD2450Parser()
        self.reader = None
        self.writer = None

    async def connect(self):
        import serial_asyncio
        self.reader, self.writer = await serial_asyncio.open_serial_connection(url=self.port, baudrate=self.baudrate)

    async def read_loop(self, queue: asyncio.Queue):
        if not self.reader:
            return

        while True:
            try:
                data = await self.reader.read(1024)
                if data:
                    targets = self.parser.process_data(data)
                    if targets:
                        # We push non-empty targets
                        if not queue.full():
                            try:
                                queue.put_nowait(targets)
                            except asyncio.QueueFull:
                                pass
            except Exception as e:
                logger.error(f"Error reading from {self.port}: {e}")
                break

    async def close(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
