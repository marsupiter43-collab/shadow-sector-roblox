import PyInstaller.__main__
import os
import sys

def build():
    # Only try to build on Windows or cross-compile environments where appropriate
    print("Starting PyInstaller build process...")

    app_path = os.path.join('z_resonance_app', 'main.py')

    PyInstaller.__main__.run([
        app_path,
        '--name=Z_RESONANCE_Simulator',
        '--onedir',
        '--windowed',
        '--noconfirm',
        '--clean',
        '--hidden-import=PyQt6',
        '--hidden-import=pyqtgraph',
        '--hidden-import=torch',
        '--hidden-import=scipy',
    ])

    print("Build complete.")

if __name__ == "__main__":
    build()
