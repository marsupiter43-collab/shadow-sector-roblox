import torch
import numpy as np
from .grid import TissueGrid

class FDTDSolver:
    def __init__(self, grid: TissueGrid, dt: float):
        self.grid = grid
        self.dt = dt
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Physical constants
        self.c0 = 299792458.0  # Speed of light in vacuum
        self.mu0 = 4 * np.pi * 1e-7
        self.eps0 = 8.8541878128e-12

        # CFL Check
        c_max = self.c0 / np.sqrt(self.grid.EPSILON_MIN)
        dt_cfl = 1.0 / (c_max * np.sqrt((1.0 / self.grid.dx**2) + (1.0 / self.grid.dy**2)))

        # Strict CFL stability condition check
        if self.dt > dt_cfl * 0.99:
            raise ValueError(f"CFL stability condition violated. Max dt: {dt_cfl:e}, given dt: {self.dt:e}")

        self.nx = grid.nx
        self.ny = grid.ny

        # Initialize fields (Ez, Hx, Hy for 2D TMz)
        self.Ez = torch.zeros((self.nx, self.ny), dtype=torch.float64, device=self.device)
        self.Hx = torch.zeros((self.nx, self.ny), dtype=torch.float64, device=self.device)
        self.Hy = torch.zeros((self.nx, self.ny), dtype=torch.float64, device=self.device)

        # Material properties tensors
        eps = torch.tensor(self.grid.epsilon_r, dtype=torch.float64, device=self.device) * self.eps0
        sig = torch.tensor(self.grid.sigma, dtype=torch.float64, device=self.device)

        # Update coefficients
        # Ez update: Ceze * Ez + Cezh * (dHy/dx - dHx/dy)
        denom = eps + sig * self.dt / 2.0
        self.Ceze = (eps - sig * self.dt / 2.0) / denom
        self.Cezh = self.dt / denom

        # Hx, Hy update: Chxh * Hx - Chxe * dEz/dy
        self.Chxh = torch.ones((self.nx, self.ny), dtype=torch.float64, device=self.device)
        self.Chxe = (self.dt / self.mu0) * torch.ones((self.nx, self.ny), dtype=torch.float64, device=self.device)
        self.Chyh = torch.ones((self.nx, self.ny), dtype=torch.float64, device=self.device)
        self.Chye = (self.dt / self.mu0) * torch.ones((self.nx, self.ny), dtype=torch.float64, device=self.device)

        self.dx = self.grid.dx
        self.dy = self.grid.dy

    def step(self):
        """Perform one FDTD time step."""
        # Update H fields
        self.Hx[:, :-1] = self.Chxh[:, :-1] * self.Hx[:, :-1] - \
                          (self.Chxe[:, :-1] / self.dy) * (self.Ez[:, 1:] - self.Ez[:, :-1])

        self.Hy[:-1, :] = self.Chyh[:-1, :] * self.Hy[:-1, :] + \
                          (self.Chye[:-1, :] / self.dx) * (self.Ez[1:, :] - self.Ez[:-1, :])

        # Absorbing Boundary Conditions (Mur 1st order)
        # Assuming open boundary space to avoid reflection from edges
        # Just simple ABC for safety (perfect PML would be ideal, but Mur suffices for core validation)
        # Mur ABC for Ez at the boundaries

        # Save previous Ez
        Ez_prev = self.Ez.clone()

        # Update Ez field
        self.Ez[1:-1, 1:-1] = self.Ceze[1:-1, 1:-1] * self.Ez[1:-1, 1:-1] + \
                              self.Cezh[1:-1, 1:-1] * (
                                  (self.Hy[1:-1, 1:-1] - self.Hy[:-2, 1:-1]) / self.dx -
                                  (self.Hx[1:-1, 1:-1] - self.Hx[1:-1, :-2]) / self.dy
                              )

        # Apply Mur 1st order ABC
        c = self.c0 / np.sqrt(self.grid.EPSILON_MIN)
        coeff_x = (c * self.dt - self.dx) / (c * self.dt + self.dx)
        coeff_y = (c * self.dt - self.dy) / (c * self.dt + self.dy)

        # Left (x=0)
        self.Ez[0, 1:-1] = Ez_prev[1, 1:-1] + coeff_x * (self.Ez[1, 1:-1] - Ez_prev[0, 1:-1])
        # Right (x=nx-1)
        self.Ez[-1, 1:-1] = Ez_prev[-2, 1:-1] + coeff_x * (self.Ez[-2, 1:-1] - Ez_prev[-1, 1:-1])
        # Bottom (y=0)
        self.Ez[1:-1, 0] = Ez_prev[1:-1, 1] + coeff_y * (self.Ez[1:-1, 1] - Ez_prev[1:-1, 0])
        # Top (y=ny-1)
        self.Ez[1:-1, -1] = Ez_prev[1:-1, -2] + coeff_y * (self.Ez[1:-1, -2] - Ez_prev[1:-1, -1])
