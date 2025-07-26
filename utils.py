"""
Utility functions and configuration management
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any
import sys

def setup_logging(log_level: str = 'INFO'):
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='[%(asctime)s] [%(name)s] [%(levelname)s] - %(message)s',
        #format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'autocorrect.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific loggers to WARNING to reduce noise
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('pynput').setLevel(logging.WARNING)

def load_config(config_path: str = 'config.json') -> Dict[str, Any]:
    """Load configuration from JSON file"""
    default_config = {
        'auto_start': False,
        'minimize_to_tray': True,
        'default_tone': 'neutral',
        'default_formality': 'medium',
        'enable_spelling': True,
        'enable_grammar': True,
        'enable_style': False,
        'use_ml_corrections': True,
        'ml_confidence_threshold': 0.7,
        'learn_from_corrections': True,
        'adapt_to_style': True,
        'processing_delay': 100,
        'log_level': 'INFO',
        'ml_model': 'facebook/bart-base'
    }
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                default_config.update(config)
        
        return default_config
        
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        return default_config

def save_config(config: Dict[str, Any], config_path: str = 'config.json'):
    """Save configuration to JSON file"""
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logging.info("Configuration saved successfully")
        
    except Exception as e:
        logging.error(f"Failed to save config: {e}")

def get_app_data_dir() -> Path:
    """Get application data directory"""
    if os.name == 'nt':  # Windows
        app_data = os.environ.get('APPDATA', '')
        if app_data:
            return Path(app_data) / 'IntelligentAutocorrect'
    
    # Fallback to current directory
    return Path.cwd()

def ensure_dependencies():
    """Check and install required dependencies"""
    required_packages = [
        'pynput',
        'pyautogui',
        'pyperclip',
        'pystray',
        'pillow',
        'psutil'
    ]
    
    optional_packages = [
        'transformers',
        'torch',
        'win32gui',
        'win32api',
        'win32clipboard'
    ]
    
    missing_required = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_required.append(package)
    
    for package in optional_packages:
        try:
            __import__(package)
        except ImportError:
            missing_optional.append(package)
    
    if missing_required:
        print(f"Missing required packages: {', '.join(missing_required)}")
        print("Please install them using: pip install " + ' '.join(missing_required))
        return False
    
    if missing_optional:
        print(f"Missing optional packages: {', '.join(missing_optional)}")
        print("Some features may not be available. Install with: pip install " + ' '.join(missing_optional))
    
    return True

def create_startup_shortcut():
    """Create Windows startup shortcut"""
    try:
        import winshell
        from win32com.client import Dispatch
        
        startup_folder = winshell.startup()
        shortcut_path = os.path.join(startup_folder, "Intelligent Autocorrect.lnk")
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = sys.executable
        shortcut.Arguments = os.path.abspath(__file__)
        shortcut.WorkingDirectory = os.path.dirname(os.path.abspath(__file__))
        shortcut.IconLocation = sys.executable
        shortcut.save()
        
        return True
        
    except Exception as e:
        logging.error(f"Failed to create startup shortcut: {e}")
        return False

def remove_startup_shortcut():
    """Remove Windows startup shortcut"""
    try:
        import winshell
        
        startup_folder = winshell.startup()
        shortcut_path = os.path.join(startup_folder, "Intelligent Autocorrect.lnk")
        
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
            return True
        
    except Exception as e:
        logging.error(f"Failed to remove startup shortcut: {e}")
        return False

def check_admin_privileges():
    """Check if running with administrator privileges"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def get_system_info() -> Dict[str, str]:
    """Get system information for debugging"""
    import platform
    import psutil
    
    return {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'cpu_count': str(psutil.cpu_count()),
        'memory_total': format_file_size(psutil.virtual_memory().total),
        'memory_available': format_file_size(psutil.virtual_memory().available)
    }
