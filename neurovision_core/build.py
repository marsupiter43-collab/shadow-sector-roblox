import PyInstaller.__main__
import os
import shutil

def build():
    print("Starting NeuroVision Core build process...")

    # Ensure assets directory exists for PyInstaller to copy
    os.makedirs('assets', exist_ok=True)

    # Ensure config exists
    if not os.path.exists('config.yaml'):
        print("Warning: config.yaml not found. Creating default.")
        with open('config.yaml', 'w') as f:
            f.write("# Default Config\n")

    # PyInstaller arguments
    args = [
        'main.py',
        '--name=NeuroVisionCore',
        '--noconsole',
        '--onedir', # or --onefile if preferred, onedir is faster to launch and easier for config
        '--add-data=config.yaml;.',
        '--add-data=assets;assets',
        '--clean'
    ]

    # Run PyInstaller
    PyInstaller.__main__.run(args)

    print("Build complete. Output is in the 'dist' directory.")

if __name__ == "__main__":
    build()
