import numpy as np

class TissueGrid:
    def __init__(self, nx: int, ny: int, dx: float, dy: float):
        self.nx = nx
        self.ny = ny
        self.dx = dx
        self.dy = dy

        # Medical physical bounds validation constants
        self.EPSILON_MIN = 1.0    # Vacuum
        self.EPSILON_MAX = 100.0  # Max realistic relative permittivity for tissue
        self.SIGMA_MIN = 0.0      # Perfect dielectric
        self.SIGMA_MAX = 5.0      # Max realistic conductivity for tissue (S/m)

        self.epsilon_r = np.ones((self.nx, self.ny), dtype=np.float64)
        self.sigma = np.zeros((self.nx, self.ny), dtype=np.float64)

        self.target_coord = (self.nx // 2, self.ny // 2)

    def validate_bounds(self):
        """Strict validation of tissue bounds to prevent unphysical simulation drift."""
        if np.any(self.epsilon_r < self.EPSILON_MIN) or np.any(self.epsilon_r > self.EPSILON_MAX):
            raise ValueError(f"Permittivity out of biological bounds [{self.EPSILON_MIN}, {self.EPSILON_MAX}].")
        if np.any(self.sigma < self.SIGMA_MIN) or np.any(self.sigma > self.SIGMA_MAX):
            raise ValueError(f"Conductivity out of biological bounds [{self.SIGMA_MIN}, {self.SIGMA_MAX}].")

    def apply_preset(self, preset_name: str):
        if preset_name == "Homogeneous Tissue":
            self.epsilon_r[:, :] = 50.0
            self.sigma[:, :] = 0.5
        elif preset_name == "Deep Target behind Dense Bone Barrier":
            self.epsilon_r[:, :] = 50.0
            self.sigma[:, :] = 0.5

            # Bone barrier
            bone_start = int(self.nx * 0.3)
            bone_end = int(self.nx * 0.4)
            self.epsilon_r[bone_start:bone_end, :] = 12.0
            self.sigma[bone_start:bone_end, :] = 0.05

        else:
            raise ValueError(f"Unknown preset: {preset_name}")

        self.validate_bounds()
