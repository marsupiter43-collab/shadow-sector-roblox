import numpy as np
from scipy.optimize import linear_sum_assignment
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Point2D:
    x: float
    y: float

@dataclass
class TriangulatedTarget:
    x: float
    y: float
    speed_x: float
    speed_y: float
    sources: int # 1 for single radar, 2 for stereo

class StereoTriangulator:
    def __init__(self, baseline_mm: float = 150.0):
        self.baseline_mm = baseline_mm
        # Left radar is at -baseline/2, Right radar is at +baseline/2
        self.radar_l_x = -baseline_mm / 2.0
        self.radar_r_x = baseline_mm / 2.0
        self.gate_threshold_mm = 250.0 # 25 cm gate

    def associate_targets(self, targets_l: List[Point2D], targets_r: List[Point2D]) -> List[tuple[Optional[Point2D], Optional[Point2D]]]:
        if not targets_l and not targets_r:
            return []

        if not targets_l:
            return [(None, tr) for tr in targets_r]

        if not targets_r:
            return [(tl, None) for tl in targets_l]

        # Cost matrix: distance between left and right targets
        # We need to project them to a common frame first.
        # But wait, radar gives X, Y relative to itself.
        # Left radar X_global = X_local + radar_l_x
        # Right radar X_global = X_local + radar_r_x

        pts_l = np.array([[t.x + self.radar_l_x, t.y] for t in targets_l])
        pts_r = np.array([[t.x + self.radar_r_x, t.y] for t in targets_r])

        # Calculate pairwise Euclidean distances
        cost_matrix = np.linalg.norm(pts_l[:, np.newaxis] - pts_r, axis=2)

        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        associations = []
        matched_l = set()
        matched_r = set()

        for r, c in zip(row_ind, col_ind):
            if cost_matrix[r, c] <= self.gate_threshold_mm:
                associations.append((targets_l[r], targets_r[c]))
                matched_l.add(r)
                matched_r.add(c)

        # Add unmatched
        for i in range(len(targets_l)):
            if i not in matched_l:
                associations.append((targets_l[i], None))

        for j in range(len(targets_r)):
            if j not in matched_r:
                associations.append((None, targets_r[j]))

        return associations

    def resolve_intersecting_arcs(self, target_l: Point2D, target_r: Point2D) -> Point2D:
        """
        Resolves intersecting distance arcs to reduce lateral positioning uncertainty.
        Given distances d_l and d_r from two radars, find the intersection.
        """
        # Distances
        d_l = np.sqrt(target_l.x**2 + target_l.y**2)
        d_r = np.sqrt(target_r.x**2 + target_r.y**2)

        d = self.baseline_mm

        # Check for valid triangle
        if d_l + d_r < d or abs(d_l - d_r) > d:
            # Cannot form a triangle, fallback to average
            x = ((target_l.x + self.radar_l_x) + (target_r.x + self.radar_r_x)) / 2.0
            y = (target_l.y + target_r.y) / 2.0
            return Point2D(x, y)

        # Using law of cosines to find coordinates
        # Let radars be at (-d/2, 0) and (d/2, 0)
        # x^2 + y^2 = d_l^2 (from left radar, shifted origin)
        # So in local coordinates where left radar is (0,0):
        # x_local = (d_l^2 - d_r^2 + d^2) / (2 * d)
        # y_local = sqrt(d_l^2 - x_local^2)

        x_local = (d_l**2 - d_r**2 + d**2) / (2 * d)

        # Avoid sqrt domain error due to floating point inaccuracies
        val = d_l**2 - x_local**2
        if val < 0:
            val = 0
        y_local = np.sqrt(val)

        # Shift to global origin (center between radars)
        x_global = x_local - d/2.0
        y_global = y_local

        return Point2D(x_global, y_global)

    def triangulate(self, targets_l: List[Point2D], targets_r: List[Point2D]) -> List[TriangulatedTarget]:
        associations = self.associate_targets(targets_l, targets_r)

        results = []
        for tl, tr in associations:
            if tl and tr:
                # Stereo matched
                pt = self.resolve_intersecting_arcs(tl, tr)
                # Approximate speeds as average if available (not fully implemented here since Point2D lacks speed)
                results.append(TriangulatedTarget(x=pt.x, y=pt.y, speed_x=0, speed_y=0, sources=2))
            elif tl:
                # Monocular left
                results.append(TriangulatedTarget(x=tl.x + self.radar_l_x, y=tl.y, speed_x=0, speed_y=0, sources=1))
            elif tr:
                # Monocular right
                results.append(TriangulatedTarget(x=tr.x + self.radar_r_x, y=tr.y, speed_x=0, speed_y=0, sources=1))

        return results
