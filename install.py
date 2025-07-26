"""
Installation script for Intelligent Autocorrect System
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install required packages"""
    print("Installing Intelligent Autocorrect System...")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        return False
    
    # Install requirements
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("Error: requirements.txt not found")
        return False
    
    try:
        print("Installing dependencies...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        
        print("\n✓ Dependencies installed successfully")
        
        # Create necessary directories
        print("Creating application directories...")
        
        directories = ["logs", "data", "exports"]
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
        
        print("✓ Directories created")
        
        # Test imports
        print("Testing imports...")
        
        required_modules = [
            "pynput", "pyautogui", "pyperclip", "pystray", 
            "PIL", "psutil", "sqlite3", "tkinter"
        ]
        
        for module in required_modules:
            try:
                __import__(module)
                print(f"✓ {module}")
            except ImportError as e:
                print(f"✗ {module}: {e}")
                return False
        
        # Test optional modules
        print("\nTesting optional modules...")
        
        optional_modules = ["transformers", "torch", "win32gui"]
        
        for module in optional_modules:
            try:
                __import__(module)
                print(f"✓ {module}")
            except ImportError:
                print(f"- {module} (optional)")
        
        print("\n" + "=" * 50)
        print("Installation completed successfully!")
        print("\nTo start the application, run:")
        print("python main.py")
        print("\nFor help and documentation, see README.md")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False
    except Exception as e:
        print(f"Installation error: {e}")
        return False

if __name__ == "__main__":
    success = install_requirements()
    if not success:
        sys.exit(1)
