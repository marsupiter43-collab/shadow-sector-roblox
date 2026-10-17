import pytest
import numpy as np
import torch
from z_resonance_app.engine.grid import TissueGrid
from z_resonance_app.engine.fdtd import FDTDSolver
from z_resonance_app.engine.optimizer import PhaseOptimizer

def test_grid_bounds_validation():
    grid = TissueGrid(nx=50, ny=50, dx=1e-3, dy=1e-3)
    grid.epsilon_r[0, 0] = 0.5  # Below vacuum
    with pytest.raises(ValueError):
        grid.validate_bounds()

def test_fdtd_cfl_condition():
    grid = TissueGrid(nx=50, ny=50, dx=1e-3, dy=1e-3)
    # Give it an impossibly large time step to force CFL violation
    dt = 1.0
    with pytest.raises(ValueError):
        FDTDSolver(grid=grid, dt=dt)

def test_safety_cutoff():
    grid = TissueGrid(nx=50, ny=50, dx=1e-3, dy=1e-3)
    # Safe dt
    c_max = 299792458.0 / np.sqrt(grid.EPSILON_MIN)
    dt_cfl = 1.0 / (c_max * np.sqrt((1.0 / grid.dx**2) + (1.0 / grid.dy**2)))

    solver = FDTDSolver(grid=grid, dt=dt_cfl * 0.95)

    # Very low safety threshold to trigger it easily
    optimizer = PhaseOptimizer(solver=solver, safety_threshold=1e-6)

    # Inject large field in healthy area
    solver.Ez[5, 5] = 100.0

    with pytest.raises(RuntimeError) as excinfo:
        optimizer.check_safety()

    assert "SAFETY CUTOFF TRIPPED" in str(excinfo.value)
