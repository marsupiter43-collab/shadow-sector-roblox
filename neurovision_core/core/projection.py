import numpy as np
from typing import Tuple, Optional

class CameraProjector:
    def __init__(self, intrinsic_k: list[list[float]]):
        self.K = np.array(intrinsic_k, dtype=np.float32)

        # Extrinsic calibration: mapping radar (X, Y, Z_est) to Camera (X_c, Y_c, Z_c)
        # Radar coordinates:
        # X: lateral (left/right)
        # Y: distance (forward)
        # Z: height (up/down)
        # Camera coordinates:
        # X_c: right
        # Y_c: down
        # Z_c: forward

        # Rotation matrix (assuming camera is aligned with radar but axes differ)
        # R = [1  0  0]
        #     [0  0 -1]
        #     [0  1  0]
        # Wait, if radar Y is forward, and Z is up.
        # Cam Z is forward -> Z_c = Y
        # Cam Y is down -> Y_c = -Z
        # Cam X is right -> X_c = X
        self.R = np.array([
            [1, 0, 0],
            [0, 0, -1],
            [0, 1, 0]
        ], dtype=np.float32)

        # Translation vector (assuming camera is mounted 100mm above radar)
        self.t = np.array([[0], [-100], [0]], dtype=np.float32)

        # Extrinsic matrix [R|t]
        self.extrinsic = np.hstack((self.R, self.t))

        # Projection matrix P = K * [R|t]
        self.P = self.K @ self.extrinsic

    def project_point(self, x: float, y: float, z: float) -> Optional[Tuple[int, int]]:
        """
        Project 3D radar point to 2D camera plane.
        """
        # Homogeneous 3D point
        point_3d = np.array([[x], [y], [z], [1.0]], dtype=np.float32)

        # Project
        point_2d = self.P @ point_3d

        w = point_2d[2, 0]
        if w <= 0:
            return None # Behind camera

        u = int(point_2d[0, 0] / w)
        v = int(point_2d[1, 0] / w)

        return (u, v)

    def generate_3d_bbox(self, x: float, y: float, vx: float, vy: float) -> list[Tuple[int, int]]:
        """
        Generates 2D screen coordinates for a 3D wireframe bounding box.
        Estimates human height and width. Extrapolates orientation based on velocity.
        """
        points = []
        # Approximate human dimensions in mm
        width = 600.0
        height = 1800.0
        depth = 400.0

        # We assume target base is at z = -height/2 relative to radar if radar is at chest height
        # Let's say radar is at z=900. Base is z=-900, top is z=900.
        z_min = -900.0
        z_max = 900.0

        # Calculate yaw angle from velocity vector
        speed = np.sqrt(vx**2 + vy**2)
        yaw = 0.0
        if speed > 10.0: # Only rotate if moving significantly
            yaw = np.arctan2(vy, vx) - np.pi/2 # Assuming facing direction is perpendicular to lateral movement

        # Rotation matrix for target
        cy, sy = np.cos(yaw), np.sin(yaw)
        R_yaw = np.array([
            [cy, -sy, 0],
            [sy, cy, 0],
            [0, 0, 1]
        ])

        # 8 corners of the bounding box
        corners = [
            np.array([width/2, depth/2, z_min]),
            np.array([-width/2, depth/2, z_min]),
            np.array([-width/2, -depth/2, z_min]),
            np.array([width/2, -depth/2, z_min]),
            np.array([width/2, depth/2, z_max]),
            np.array([-width/2, depth/2, z_max]),
            np.array([-width/2, -depth/2, z_max]),
            np.array([width/2, -depth/2, z_max])
        ]

        for corner in corners:
            # Rotate corner
            rotated = R_yaw @ corner

            # Translate to target position
            px = x + rotated[0]
            py = y + rotated[1]
            pz = rotated[2]

            proj = self.project_point(px, py, pz)
            if proj:
                points.append(proj)

        return points
