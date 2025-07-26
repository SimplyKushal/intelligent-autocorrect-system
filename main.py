"""
Intelligent Autocorrect System - Main Entry Point
A system-wide text correction and rephrasing tool for Windows
"""

import sys
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
import json
import logging

import keyboard_monitor
from keyboard_monitor import KeyboardMonitor
from text_processor import TextProcessor
from memory_module import MemoryModule
from ui_components import SystemTrayUI, ConfigWindow
from utils import setup_logging, load_config, save_config

class IntelligentAutocorrectSystem:
    def __init__(self):
        self.config = load_config()
        setup_logging(self.config.get('log_level', 'INFO'))
        self.logger = logging.getLogger("main")
        #self.logger = logging.getLogger(__name__)
        
        # Initialize core components
        self.memory_module = MemoryModule()
        self.text_processor = TextProcessor(self.memory_module, self.config)
        self.keyboard_monitor = KeyboardMonitor(self.on_text_input)
        
        # UI components
        self.system_tray = None
        self.config_window = None
        
        # State management
        self.is_running = False
        self.current_buffer = ""
        self.last_correction_time = 0
        
        self.logger.info("Autocorrect system initialized and running")
    
    def start(self):
        """Start the autocorrect system"""
        try:
            self.is_running = True
            
            # Start keyboard monitoring in separate thread
            self.keyboard_thread = threading.Thread(
                target=self.keyboard_monitor.start_monitoring,
                daemon=True
            )
            self.keyboard_thread.start()
            
            # Initialize system tray UI
            self.system_tray = SystemTrayUI(self)
            
            self.logger.info("Autocorrect system started successfully")
            
            # Start the main UI loop
            self.system_tray.run()
            
        except Exception as e:
            self.logger.error(f"Failed to start system: {e}")
            messagebox.showerror("Error", f"Failed to start autocorrect system: {e}")
    
    def stop(self):
        """Stop the autocorrect system"""
        self.is_running = False
        if hasattr(self, 'keyboard_monitor'):
            self.keyboard_monitor.stop_monitoring()
        
        self.logger.info("Autocorrect system stopped")
    
    def on_text_input(self, text_data):
        """Handle text input from keyboard monitor"""
        if not self.is_running:
            return
        
        try:
            word = text_data.get('word', '')
            context = text_data.get('context', '')
            trigger_type = text_data.get('trigger', 'space')
            
            if len(word) < 2:  # Skip very short words
                return
            
            # Process the text for corrections/improvements
            result = self.text_processor.process_text(
                word=word,
                context=context,
                tone=self.config.get('default_tone', 'neutral'),
                formality=self.config.get('default_formality', 'medium')
            )
            
            if result and result['corrected_text'] != word:
                # Apply the correction
                self.apply_correction(word, result['corrected_text'], result)
                
        except Exception as e:
            self.logger.error(f"Error processing text input: {e}")
    
    def apply_correction(self, original_word, corrected_text, correction_data):
        """Apply text correction by replacing the original word"""
        try:
            # Prevent rapid corrections
            current_time = time.time()
            if current_time - self.last_correction_time < 0.5:
                return
            
            self.last_correction_time = current_time
            
            # Use text injection to replace the word
            from text_injector import TextInjector
            injector = TextInjector()
            
            success = injector.replace_text(original_word, corrected_text)
            
            if success:
                # Log the correction
                self.memory_module.log_correction(
                    original=original_word,
                    corrected=corrected_text,
                    correction_type=correction_data.get('type', 'autocorrect'),
                    confidence=correction_data.get('confidence', 0.0)
                )
                
                self.logger.info(f"Applied correction: '{original_word}' -> '{corrected_text}'")
            
        except Exception as e:
            self.logger.error(f"Failed to apply correction: {e}")
    
    def toggle_system(self):
        """Toggle the autocorrect system on/off"""
        if self.is_running:
            self.keyboard_monitor.pause_monitoring()
            self.is_running = False
            self.logger.info("System paused")
        else:
            self.keyboard_monitor.resume_monitoring()
            self.is_running = True
            self.logger.info("System resumed")
    
    def show_config_window(self):
        """Show the configuration window"""
        if not self.config_window:
            self.config_window = ConfigWindow(self)
        self.config_window.show()
    
    def update_config(self, new_config):
        """Update system configuration"""
        self.config.update(new_config)
        save_config(self.config)
        self.text_processor.update_config(self.config)
        self.logger.info("Configuration updated")

#logger = logging.getLogger("main")
def shutdown():
        logger = logging.getLogger("main")
        logger.info("Shutting down autocorrect system...")

        try:
            keyboard_monitor.stop_monitoring()
            # Add other cleanup tasks here, like stopping tray icon if you use one later
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

def main():
    """Main entry point"""
    try:
        import psutil
        current_process = psutil.Process()
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if (proc.info['name'] == current_process.name() and
                proc.info['pid'] != current_process.pid and
                'main.py' in ' '.join(proc.info['cmdline'] or [])):
                messagebox.showwarning(
                    "Already Running",
                    "Intelligent Autocorrect System is already running!"
                )
                return

        # Create and start the system
        system = IntelligentAutocorrectSystem()
        system.start()

    except KeyboardInterrupt:
        print("\nShutting down...")
        shutdown(system)  # graceful exit
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        messagebox.showerror("Fatal Error", f"System crashed: {e}")
        shutdown(system)  # also cleanup on unexpected crash


# def main():
#     """Main entry point"""
#     try:
#         # Check if already running
#         import psutil
#         current_process = psutil.Process()
#         for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
#             if (proc.info['name'] == current_process.name() and
#                 proc.info['pid'] != current_process.pid and
#                 'main.py' in ' '.join(proc.info['cmdline'] or [])):
#                 messagebox.showwarning(
#                     "Already Running",
#                     "Intelligent Autocorrect System is already running!"
#                 )
#                 return
#
#         # Create and start the system
#         system = IntelligentAutocorrectSystem()
#         system.start()
#
#     except KeyboardInterrupt:
#         print("\nShutting down...")
#     except Exception as e:
#         logging.error(f"Fatal error: {e}")
#         messagebox.showerror("Fatal Error", f"System crashed: {e}")

if __name__ == "__main__":
    main()
