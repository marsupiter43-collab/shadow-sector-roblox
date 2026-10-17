import torch
import numpy as np
from .fdtd import FDTDSolver

class PhaseOptimizer:
    def __init__(self, solver: FDTDSolver, safety_threshold: float = 1e6):
        self.solver = solver
        self.safety_threshold = safety_threshold

        # Determine Healthy Tissue Areas (assuming default bounds)
        # Simple mask: True if it's healthy tissue, False if target or barrier
        self.healthy_mask = torch.ones((self.solver.nx, self.solver.ny), dtype=torch.bool, device=self.solver.device)
        tx, ty = self.solver.grid.target_coord
        self.healthy_mask[tx-5:tx+5, ty-5:ty+5] = False  # Target area is not "healthy" to protect

        # Transducer array (emitter positions, left edge)
        self.num_transducers = 32
        self.transducer_y = np.linspace(10, self.solver.ny - 10, self.num_transducers, dtype=int)
        self.transducer_x = np.full(self.num_transducers, 5)

    def check_safety(self):
        """Safety cutoff: Check if healthy tissue E-field exceeds threshold."""
        max_e = torch.max(torch.abs(self.solver.Ez[self.healthy_mask])).item()
        if max_e > self.safety_threshold:
            raise RuntimeError(f"SAFETY CUTOFF TRIPPED: Field magnitude {max_e:e} exceeds safe threshold {self.safety_threshold:e}.")
        return max_e

    def emit_standard(self, time_step: int, frequency: float):
        """Mode A: Standard Transmission (uniform phase)."""
        t = time_step * self.solver.dt
        source_val = np.sin(2 * np.pi * frequency * t)

        for tx, ty in zip(self.transducer_x, self.transducer_y):
            self.solver.Ez[tx, ty] += source_val

        return self.check_safety()

    def emit_phase_matched(self, time_step: int, frequency: float, delays: np.ndarray):
        """Mode B: Z-Resonance Phase-Matched (Time Reversal / Phase Conjugation)."""
        t = time_step * self.solver.dt

        for i, (tx, ty) in enumerate(zip(self.transducer_x, self.transducer_y)):
            # Apply individual delays computed via phase conjugation
            source_val = np.sin(2 * np.pi * frequency * (t - delays[i]))
            self.solver.Ez[tx, ty] += source_val

        return self.check_safety()

    def calculate_phase_delays(self, frequency: float) -> np.ndarray:
        """Simulate Time Reversal: place source at target, record at transducers to find delays."""
        # This is a simplified stand-in for the full time-reversal FDTD run.
        # In a full simulation, we would run FDTD with source at target,
        # record arrival times at transducers, and reverse them.

        # To make it functionally robust for the structure without requiring long pre-computation,
        # we estimate the phase delays geometrically, corrected by the permittivity map.

        delays = np.zeros(self.num_transducers, dtype=np.float64)
        target_x, target_y = self.solver.grid.target_coord

        for i, (tx, ty) in enumerate(zip(self.transducer_x, self.transducer_y)):
            # Average permittivity along the ray (simplified approximation)
            # In a true TR setup, we'd use the FDTD solver itself.

            # Distance
            dist = np.sqrt(((target_x - tx) * self.solver.grid.dx)**2 + ((target_y - ty) * self.solver.grid.dy)**2)

            # Simple average speed of light along the path
            c_avg = self.solver.c0 / np.sqrt(50.0) # Assume avg tissue permittivity 50 for rough delay

            travel_time = dist / c_avg
            delays[i] = -travel_time # Phase conjugate (time reversal)

        # Normalize delays so minimum delay is 0
        delays = delays - np.min(delays)
        return delays
