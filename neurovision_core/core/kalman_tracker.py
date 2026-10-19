import numpy as np
from scipy.stats import chi2
import time

class EKFTracker:
    def __init__(self, id: int, initial_state: np.ndarray, dt: float = 0.033):
        self.id = id
        self.dt = dt
        # State vector: [x, y, vx, vy, ax, ay]^T
        self.x = initial_state.reshape(6, 1)

        # State transition matrix (Constant Acceleration Model)
        self.F = np.array([
            [1, 0, dt, 0, 0.5*dt**2, 0],
            [0, 1, 0, dt, 0, 0.5*dt**2],
            [0, 0, 1, 0, dt, 0],
            [0, 0, 0, 1, 0, dt],
            [0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 1]
        ])

        # Measurement matrix (observing x, y)
        self.H = np.array([
            [1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0]
        ])

        # Initial Covariance Matrix
        self.P = np.eye(6) * 1000.0

        # Process Noise Covariance (Q)
        q = 0.1 # Tuned for indoor micro-movements
        self.Q = np.eye(6) * q

        # Measurement Noise Covariance (R)
        r = 10.0 # Tuned for multipath reflections
        self.R = np.eye(2) * r

        self.last_update_time = time.time()
        self.missed_updates = 0

    def predict(self, dt: float = None):
        if dt is not None:
            self.dt = dt
            self.F[0, 2] = dt
            self.F[1, 3] = dt
            self.F[0, 4] = 0.5 * dt**2
            self.F[1, 5] = 0.5 * dt**2
            self.F[2, 4] = dt
            self.F[3, 5] = dt

        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q

    def update(self, z: np.ndarray) -> bool:
        """
        Returns True if measurement was accepted, False if rejected by Mahalanobis gate.
        z is a 2x1 array [x, y]^T
        """
        # Innovation
        y = z.reshape(2, 1) - self.H @ self.x

        # Innovation covariance
        S = self.H @ self.P @ self.H.T + self.R

        # Mahalanobis distance
        try:
            S_inv = np.linalg.inv(S)
        except np.linalg.LinAlgError:
            S_inv = np.linalg.pinv(S)

        d_m = float(y.T @ S_inv @ y)

        # 99% Chi-square test (9.21 for 2 degrees of freedom)
        if d_m > 9.21:
            return False # Reject outlier (multipath ghost)

        # Kalman Gain
        K = self.P @ self.H.T @ S_inv

        # Update State
        self.x = self.x + K @ y

        # Update Covariance
        I = np.eye(6)
        self.P = (I - K @ self.H) @ self.P

        self.last_update_time = time.time()
        self.missed_updates = 0
        return True

class TargetManager:
    def __init__(self):
        self.trackers = {}
        self.next_id = 0
        self.max_missed_updates = 10

    def process_measurements(self, measurements: list[np.ndarray]):
        # Very basic nearest neighbor assignment to trackers
        # In a full system, you would use Hungarian algorithm here as well

        assigned_measurements = set()

        for tid, tracker in self.trackers.items():
            tracker.predict()

            best_m_idx = -1
            best_dist = float('inf')

            for i, m in enumerate(measurements):
                if i in assigned_measurements:
                    continue
                dist = np.linalg.norm(tracker.x[0:2].flatten() - m)
                if dist < best_dist:
                    best_dist = dist
                    best_m_idx = i

            if best_m_idx != -1 and best_dist < 500: # 50cm gate for tracking
                accepted = tracker.update(measurements[best_m_idx])
                if accepted:
                    assigned_measurements.add(best_m_idx)
                else:
                    tracker.missed_updates += 1
            else:
                tracker.missed_updates += 1

        # Remove stale tracks
        stale_tids = [tid for tid, tracker in self.trackers.items() if tracker.missed_updates > self.max_missed_updates]
        for tid in stale_tids:
            del self.trackers[tid]

        # Spawn new tracks
        for i, m in enumerate(measurements):
            if i not in assigned_measurements:
                initial_state = np.array([m[0], m[1], 0, 0, 0, 0])
                self.trackers[self.next_id] = EKFTracker(self.next_id, initial_state)
                self.next_id += 1
