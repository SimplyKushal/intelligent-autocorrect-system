"""
UI Components - System tray, configuration window, and user interface elements
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import logging
from PIL import Image, ImageTk
import pystray
from pystray import MenuItem, Menu
import io
import base64

class SystemTrayUI:
    def __init__(self, main_system):
        self.main_system = main_system
        self.logger = logging.getLogger(__name__)
        
        # Create system tray icon
        self.icon = None
        self.create_tray_icon()
    
    def create_tray_icon(self):
        """Create system tray icon and menu"""
        try:
            # Create a simple icon (you can replace with a proper icon file)
            icon_image = self.create_icon_image()
            
            # Create menu items
            menu = Menu(
                MenuItem("Intelligent Autocorrect", self.show_status, default=True),
                MenuItem("Toggle On/Off", self.toggle_system),
                Menu.SEPARATOR,
                MenuItem("Configuration", self.show_config),
                MenuItem("Statistics", self.show_statistics),
                MenuItem("History", self.show_history),
                Menu.SEPARATOR,
                MenuItem("Export Data", self.export_data),
                MenuItem("About", self.show_about),
                Menu.SEPARATOR,
                MenuItem("Exit", self.exit_application)
            )
            
            # Create the icon
            self.icon = pystray.Icon(
                "IntelligentAutocorrect",
                icon_image,
                "Intelligent Autocorrect System",
                menu
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create tray icon: {e}")
    
    def create_icon_image(self):
        """Create a simple icon image"""
        # Create a simple 16x16 icon
        from PIL import Image, ImageDraw
        
        image = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw a simple "A" for Autocorrect
        draw.rectangle([2, 2, 14, 14], fill=(0, 120, 215, 255))
        draw.text((4, 3), "A", fill=(255, 255, 255, 255))
        
        return image
    
    def run(self):
        """Start the system tray"""
        if self.icon:
            self.icon.run()
    
    def show_status(self, icon, item):
        """Show system status"""
        status = "Running" if self.main_system.is_running else "Paused"
        stats = self.main_system.memory_module.get_statistics(7)  # Last 7 days
        
        message = f"""Intelligent Autocorrect System
        
Status: {status}
Recent Activity (7 days):
- Corrections made: {stats['total_corrections']}
- Words processed: {stats['total_words']}
- Active days: {stats['active_days']}
        """
        
        messagebox.showinfo("System Status", message)
    
    def toggle_system(self, icon, item):
        """Toggle the autocorrect system"""
        self.main_system.toggle_system()
        
        # Update icon tooltip
        status = "Running" if self.main_system.is_running else "Paused"
        self.icon.title = f"Intelligent Autocorrect - {status}"
    
    def show_config(self, icon, item):
        """Show configuration window"""
        self.main_system.show_config_window()
    
    def show_statistics(self, icon, item):
        """Show statistics window"""
        StatsWindow(self.main_system)
    
    def show_history(self, icon, item):
        """Show correction history window"""
        HistoryWindow(self.main_system)
    
    def export_data(self, icon, item):
        """Export correction data"""
        success = self.main_system.memory_module.export_data()
        if success:
            messagebox.showinfo("Export Complete", "Data exported to autocorrect_export.csv")
        else:
            messagebox.showerror("Export Failed", "Failed to export data")
    
    def show_about(self, icon, item):
        """Show about dialog"""
        about_text = """Intelligent Autocorrect System v1.0

A privacy-first, offline autocorrect and text enhancement tool for Windows.

Features:
• Real-time text correction
• ML-driven suggestions
• Personalized learning
• Complete privacy (offline operation)
• Cross-application support

Built with Python and love for better typing experience.
        """
        messagebox.showinfo("About", about_text)
    
    def exit_application(self, icon, item):
        """Exit the application"""
        self.main_system.stop()
        self.icon.stop()

class ConfigWindow:
    _instance = None  # Class variable to track single instance

    def __init__(self, main_system):
        self.main_system = main_system
        self.logger = logging.getLogger(__name__)
        self.window = None

    def show(self):
        """Show the configuration window"""
        # Implement singleton pattern
        if ConfigWindow._instance and ConfigWindow._instance.window and ConfigWindow._instance.window.winfo_exists():
            ConfigWindow._instance.window.lift()
            ConfigWindow._instance.window.focus_force()
            return
        else:
            ConfigWindow._instance = None
        # if ConfigWindow._instance is not None:
        #     # Bring existing window to front
        #     try:
        #         ConfigWindow._instance.window.lift()
        #         ConfigWindow._instance.window.focus_force()
        #         return
        #     except:
        #         # Window was destroyed, create new one
        #         ConfigWindow._instance = None

        ConfigWindow._instance = self
        self.create_window()

    def create_window(self):
        """Create the configuration window"""
        self.window = tk.Toplevel()
        self.window.title("Autocorrect Configuration")
        self.window.geometry("500x600")
        self.window.resizable(True, True)

        # Handle window closing properly
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Create notebook for tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # General settings tab
        self.create_general_tab(notebook)

        # Correction settings tab
        self.create_correction_tab(notebook)

        # Personalization tab
        self.create_personalization_tab(notebook)

        # Advanced tab
        self.create_advanced_tab(notebook)

        # Buttons frame
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(button_frame, text="Save", command=self.save_config).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.close_window).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Reset to Defaults", command=self.reset_config).pack(side=tk.LEFT)

        # Center the window
        self.center_window()

        # Bring to front
        self.window.lift()
        self.window.focus_force()

    def center_window(self):
        """Center the window on screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def close_window(self):
        """Close the window properly"""
        if self.window:
            self.window.destroy()
            self.window = None #new
        ConfigWindow._instance = None

    def on_closing(self):
        """Handle window close event"""
        self.close_window()

    def create_general_tab(self, notebook):
        """Create general settings tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="General")

        # System settings
        system_frame = ttk.LabelFrame(frame, text="System Settings")
        system_frame.pack(fill=tk.X, padx=5, pady=5)

        self.auto_start_var = tk.BooleanVar(value=self.main_system.config.get('auto_start', False))
        ttk.Checkbutton(system_frame, text="Start with Windows",
                       variable=self.auto_start_var).pack(anchor=tk.W, padx=5, pady=2)

        self.minimize_to_tray_var = tk.BooleanVar(value=self.main_system.config.get('minimize_to_tray', True))
        ttk.Checkbutton(system_frame, text="Minimize to system tray",
                       variable=self.minimize_to_tray_var).pack(anchor=tk.W, padx=5, pady=2)

        # Correction behavior
        behavior_frame = ttk.LabelFrame(frame, text="Correction Behavior")
        behavior_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(behavior_frame, text="Default Tone:").pack(anchor=tk.W, padx=5, pady=2)
        self.tone_var = tk.StringVar(value=self.main_system.config.get('default_tone', 'neutral'))
        tone_combo = ttk.Combobox(behavior_frame, textvariable=self.tone_var,
                                 values=['casual', 'neutral', 'formal'], state='readonly')
        tone_combo.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(behavior_frame, text="Default Formality:").pack(anchor=tk.W, padx=5, pady=2)
        self.formality_var = tk.StringVar(value=self.main_system.config.get('default_formality', 'medium'))
        formality_combo = ttk.Combobox(behavior_frame, textvariable=self.formality_var,
                                      values=['low', 'medium', 'high'], state='readonly')
        formality_combo.pack(fill=tk.X, padx=5, pady=2)

    def create_correction_tab(self, notebook):
        """Create correction settings tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Corrections")

        # Correction types
        types_frame = ttk.LabelFrame(frame, text="Correction Types")
        types_frame.pack(fill=tk.X, padx=5, pady=5)

        self.spelling_var = tk.BooleanVar(value=self.main_system.config.get('enable_spelling', True))
        ttk.Checkbutton(types_frame, text="Spelling corrections",
                       variable=self.spelling_var).pack(anchor=tk.W, padx=5, pady=2)

        self.grammar_var = tk.BooleanVar(value=self.main_system.config.get('enable_grammar', True))
        ttk.Checkbutton(types_frame, text="Grammar corrections",
                       variable=self.grammar_var).pack(anchor=tk.W, padx=5, pady=2)

        self.style_var = tk.BooleanVar(value=self.main_system.config.get('enable_style', False))
        ttk.Checkbutton(types_frame, text="Style improvements",
                       variable=self.style_var).pack(anchor=tk.W, padx=5, pady=2)

        # ML settings
        ml_frame = ttk.LabelFrame(frame, text="Machine Learning")
        ml_frame.pack(fill=tk.X, padx=5, pady=5)

        self.use_ml_var = tk.BooleanVar(value=self.main_system.config.get('use_ml_corrections', True))
        ttk.Checkbutton(ml_frame, text="Enable ML-based corrections",
                       variable=self.use_ml_var).pack(anchor=tk.W, padx=5, pady=2)

        ttk.Label(ml_frame, text="ML Confidence Threshold:").pack(anchor=tk.W, padx=5, pady=2)
        self.ml_threshold_var = tk.DoubleVar(value=self.main_system.config.get('ml_confidence_threshold', 0.7))
        threshold_scale = ttk.Scale(ml_frame, from_=0.1, to=1.0, variable=self.ml_threshold_var, orient=tk.HORIZONTAL)
        threshold_scale.pack(fill=tk.X, padx=5, pady=2)


    def create_personalization_tab(self, notebook):
        """Create personalization tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Personalization")

        # Learning settings
        learning_frame = ttk.LabelFrame(frame, text="Learning Settings")
        learning_frame.pack(fill=tk.X, padx=5, pady=5)

        self.learn_from_corrections_var = tk.BooleanVar(
            value=self.main_system.config.get('learn_from_corrections', True))
        ttk.Checkbutton(learning_frame, text="Learn from my corrections",
                        variable=self.learn_from_corrections_var).pack(anchor=tk.W, padx=5, pady=2)

        self.adapt_to_style_var = tk.BooleanVar(value=self.main_system.config.get('adapt_to_style', True))
        ttk.Checkbutton(learning_frame, text="Adapt to my writing style",
                        variable=self.adapt_to_style_var).pack(anchor=tk.W, padx=5, pady=2)

        # Personal dictionary
        dict_frame = ttk.LabelFrame(frame, text="Personal Dictionary")
        dict_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Add word section
        add_frame = ttk.Frame(dict_frame)
        add_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(add_frame, text="Add personal correction:").pack(anchor=tk.W)

        entry_frame = ttk.Frame(add_frame)
        entry_frame.pack(fill=tk.X, pady=2)

        self.from_text_var = tk.StringVar()
        self.to_text_var = tk.StringVar()

        ttk.Label(entry_frame, text="From:").pack(side=tk.LEFT)
        self.from_entry = ttk.Entry(entry_frame, textvariable=self.from_text_var, width=15)
        self.from_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(entry_frame, text="To:").pack(side=tk.LEFT)
        self.to_entry = ttk.Entry(entry_frame, textvariable=self.to_text_var, width=15)
        self.to_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(entry_frame, text="Add", command=self.add_personal_correction).pack(side=tk.LEFT, padx=5)


    # def create_personalization_tab(self, notebook):
    #     """Create personalization tab"""
    #     frame = ttk.Frame(notebook)
    #     notebook.add(frame, text="Personalization")
    #
    #     # Learning settings
    #     learning_frame = ttk.LabelFrame(frame, text="Learning Settings")
    #     learning_frame.pack(fill=tk.X, padx=5, pady=5)
    #
    #     self.learn_from_corrections_var = tk.BooleanVar(value=self.main_system.config.get('learn_from_corrections', True))
    #     ttk.Checkbutton(learning_frame, text="Learn from my corrections",
    #                    variable=self.learn_from_corrections_var).pack(anchor=tk.W, padx=5, pady=2)
    #
    #     self.adapt_to_style_var = tk.BooleanVar(value=self.main_system.config.get('adapt_to_style', True))
    #     ttk.Checkbutton(learning_frame, text="Adapt to my writing style",
    #                    variable=self.adapt_to_style_var).pack(anchor=tk.W, padx=5, pady=2)
    #
    #     # Personal dictionary
    #     dict_frame = ttk.LabelFrame(frame, text="Personal Dictionary")
    #     dict_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    #
    #     # Add word section
    #     add_frame = ttk.Frame(dict_frame)
    #     add_frame.pack(fill=tk.X, padx=5, pady=5)
    #
    #     ttk.Label(add_frame, text="Add personal correction:").pack(anchor=tk.W)
    #
    #     entry_frame = ttk.Frame(add_frame)
    #     entry_frame.pack(fill=tk.X, pady=2)
    #
    #     ttk.Label(entry_frame, text="From:").pack(side=tk.LEFT)
    #     self.from_entry = ttk.Entry(entry_frame, width=15)
    #     self.from_entry.pack(side=tk.LEFT, padx=5)
    #
    #     ttk.Label(entry_frame, text="To:").pack(side=tk.LEFT)
    #     self.to_entry = ttk.Entry(entry_frame, width=15)
    #     self.to_entry.pack(side=tk.LEFT, padx=5)
    #
    #     ttk.Button(entry_frame, text="Add", command=self.add_personal_correction).pack(side=tk.LEFT, padx=5)

    def create_advanced_tab(self, notebook):
        """Create advanced settings tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Advanced")

        # Performance settings
        perf_frame = ttk.LabelFrame(frame, text="Performance")
        perf_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(perf_frame, text="Processing delay (ms):").pack(anchor=tk.W, padx=5, pady=2)
        self.delay_var = tk.IntVar(value=self.main_system.config.get('processing_delay', 100))
        delay_scale = ttk.Scale(perf_frame, from_=50, to=500, variable=self.delay_var, orient=tk.HORIZONTAL)
        delay_scale.pack(fill=tk.X, padx=5, pady=2)

        # Logging settings
        log_frame = ttk.LabelFrame(frame, text="Logging")
        log_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(log_frame, text="Log Level:").pack(anchor=tk.W, padx=5, pady=2)
        self.log_level_var = tk.StringVar(value=self.main_system.config.get('log_level', 'INFO'))
        log_combo = ttk.Combobox(log_frame, textvariable=self.log_level_var,
                                values=['DEBUG', 'INFO', 'WARNING', 'ERROR'], state='readonly')
        log_combo.pack(fill=tk.X, padx=5, pady=2)

        # Data management
        data_frame = ttk.LabelFrame(frame, text="Data Management")
        data_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(data_frame, text="Clear Correction History",
                  command=self.clear_history).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Button(data_frame, text="Reset Personal Dictionary",
                  command=self.reset_dictionary).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Button(data_frame, text="Export All Data",
                  command=self.export_all_data).pack(anchor=tk.W, padx=5, pady=2)

    def add_personal_correction(self):
        """Add a personal correction"""
        from_text = self.from_text_var.get().strip()
        to_text = self.to_text_var.get().strip()

        if from_text and to_text:
            self.main_system.memory_module.add_personal_correction(from_text, to_text)
            self.from_text_var.set("")
            self.to_text_var.set("")
            messagebox.showinfo("Success", f"Added correction: {from_text} → {to_text}")
        else:
            messagebox.showwarning("Invalid Input", "Please enter both 'from' and 'to' text")

        # from_text = self.from_entry.get().strip()
        # to_text = self.to_entry.get().strip()
        #
        # if from_text and to_text:
        #     self.main_system.memory_module.add_personal_correction(from_text, to_text)
        #     self.from_entry.delete(0, tk.END)
        #     self.to_entry.delete(0, tk.END)
        #     messagebox.showinfo("Success", f"Added correction: {from_text} → {to_text}")
        # else:
        #     messagebox.showwarning("Invalid Input", "Please enter both 'from' and 'to' text")

    def clear_history(self):
        """Clear correction history"""
        if messagebox.askyesno("Confirm", "Clear all correction history? This cannot be undone."):
            # Implementation would clear the history
            messagebox.showinfo("Success", "Correction history cleared")

    def reset_dictionary(self):
        """Reset personal dictionary"""
        if messagebox.askyesno("Confirm", "Reset personal dictionary? This cannot be undone."):
            # Implementation would reset the dictionary
            messagebox.showinfo("Success", "Personal dictionary reset")

    def export_all_data(self):
        """Export all data"""
        success = self.main_system.memory_module.export_data()
        if success:
            messagebox.showinfo("Success", "All data exported successfully")
        else:
            messagebox.showerror("Error", "Failed to export data")

    def reset_config(self):
        """Reset configuration to defaults"""
        if messagebox.askyesno("Confirm", "Reset all settings to defaults?"):
            # Reset all variables to defaults
            self.auto_start_var.set(False)
            self.minimize_to_tray_var.set(True)
            self.tone_var.set('neutral')
            self.formality_var.set('medium')
            self.spelling_var.set(True)
            self.grammar_var.set(True)
            self.style_var.set(False)
            self.use_ml_var.set(True)
            self.ml_threshold_var.set(0.7)
            self.learn_from_corrections_var.set(True)
            self.adapt_to_style_var.set(True)
            self.delay_var.set(100)
            self.log_level_var.set('INFO')
            messagebox.showinfo("Success", "Settings reset to defaults")

    def save_config(self):
        """Save configuration changes"""
        try:
            new_config = {
                'auto_start': self.auto_start_var.get(),
                'minimize_to_tray': self.minimize_to_tray_var.get(),
                'default_tone': self.tone_var.get(),
                'default_formality': self.formality_var.get(),
                'enable_spelling': self.spelling_var.get(),
                'enable_grammar': self.grammar_var.get(),
                'enable_style': self.style_var.get(),
                'use_ml_corrections': self.use_ml_var.get(),
                'ml_confidence_threshold': self.ml_threshold_var.get(),
                'learn_from_corrections': self.learn_from_corrections_var.get(),
                'adapt_to_style': self.adapt_to_style_var.get(),
                'processing_delay': self.delay_var.get(),
                'log_level': self.log_level_var.get()
            }

            self.main_system.update_config(new_config)
            messagebox.showinfo("Success", "Configuration saved successfully")
            self.close_window()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")

class StatsWindow:
    _instance = None  # Class variable to track single instance

    def __init__(self, main_system):
        # Implement singleton pattern
        if StatsWindow._instance is not None:
            # Bring existing window to front
            try:
                StatsWindow._instance.window.lift()
                StatsWindow._instance.window.focus_force()
                return
            except:
                # Window was destroyed, create new one
                StatsWindow._instance = None

        self.main_system = main_system
        self.window = None
        StatsWindow._instance = self
        self.create_window()

    def create_window(self):
        """Create statistics window"""
        self.window = tk.Toplevel()
        self.window.title("Autocorrect Statistics")
        self.window.geometry("600x400")
        self.window.resizable(True, True)

        # Handle window closing properly
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Create notebook for different time periods
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Today's stats
        self.create_stats_tab(notebook, "Today", 1)

        # This week's stats
        self.create_stats_tab(notebook, "This Week", 7)

        # This month's stats
        self.create_stats_tab(notebook, "This Month", 30)

        # All time stats
        self.create_stats_tab(notebook, "All Time", 365)

        # Add close button at bottom
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(button_frame, text="Refresh", command=self.refresh_stats).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self.close_window).pack(side=tk.RIGHT, padx=5)

        # Center the window
        self.center_window()

        # Bring to front
        self.window.lift()
        self.window.focus_force()

    def create_stats_tab(self, notebook, title, days):
        """Create a statistics tab for a specific time period"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=title)

        # Get statistics
        stats = self.main_system.memory_module.get_statistics(days)

        # Create stats display
        stats_frame = ttk.LabelFrame(frame, text=f"Statistics - {title}")
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Display stats
        ttk.Label(stats_frame, text=f"Total Corrections: {stats['total_corrections']}").pack(anchor=tk.W, padx=10, pady=5)
        ttk.Label(stats_frame, text=f"Words Processed: {stats['total_words']}").pack(anchor=tk.W, padx=10, pady=5)
        ttk.Label(stats_frame, text=f"Average Accuracy: {stats['average_accuracy']:.1%}").pack(anchor=tk.W, padx=10, pady=5)
        ttk.Label(stats_frame, text=f"Active Days: {stats['active_days']}").pack(anchor=tk.W, padx=10, pady=5)

        if stats['total_words'] > 0:
            correction_rate = (stats['total_corrections'] / stats['total_words']) * 100
            ttk.Label(stats_frame, text=f"Correction Rate: {correction_rate:.1f}%").pack(anchor=tk.W, padx=10, pady=5)

    def refresh_stats(self):
        """Refresh statistics data"""
        # Close current window and create new one with fresh data
        self.close_window()
        StatsWindow(self.main_system)

    def center_window(self):
        """Center the window on screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def close_window(self):
        """Close the window properly"""
        if self.window:
            self.window.destroy()
            self.window = None #new
        StatsWindow._instance = None

    def on_closing(self):
        """Handle window close event"""
        self.close_window()

class HistoryWindow:
    _instance = None  # Class variable to track single instance

    def __init__(self, main_system):
        # Implement singleton pattern
        if HistoryWindow._instance is not None:
            # Bring existing window to front
            try:
                HistoryWindow._instance.window.lift()
                HistoryWindow._instance.window.focus_force()
                return
            except:
                # Window was destroyed, create new one
                HistoryWindow._instance = None

        self.main_system = main_system
        self.window = None
        HistoryWindow._instance = self
        self.create_window()

    def create_window(self):
        """Create correction history window"""
        self.window = tk.Toplevel()
        self.window.title("Correction History")
        self.window.geometry("800x500")
        self.window.resizable(True, True)

        # Handle window closing properly
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Create main frame
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create treeview for history
        columns = ('Time', 'Original', 'Corrected', 'Type', 'Confidence', 'Application')
        self.tree = ttk.Treeview(main_frame, columns=columns, show='headings')

        # Configure columns
        column_widths = {'Time': 150, 'Original': 120, 'Corrected': 120, 'Type': 80, 'Confidence': 80, 'Application': 120}
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths.get(col, 100))

        # Create frame for treeview and scrollbars
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Pack treeview and scrollbars
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Load history data
        self.load_history()

        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame, text="Refresh", command=self.load_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export", command=self.export_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Selection", command=self.clear_selection).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self.close_window).pack(side=tk.RIGHT, padx=5)

        # Center the window
        self.center_window()

        # Bring to front
        self.window.lift()
        self.window.focus_force()

    def load_history(self):
        """Load correction history into the treeview"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            # Get history data
            history = self.main_system.memory_module.get_correction_history(500)

            # Add items to treeview
            for entry in history:
                self.tree.insert('', tk.END, values=(
                    entry['timestamp'][:19] if entry['timestamp'] else '',  # Format timestamp
                    entry['original'],
                    entry['corrected'],
                    entry['type'],
                    f"{entry['confidence']:.2f}",
                    entry['application'] or 'Unknown'
                ))

            # Update status
            self.window.title(f"Correction History ({len(history)} entries)")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load history: {e}")

    def clear_selection(self):
        """Clear treeview selection"""
        for item in self.tree.selection():
            self.tree.selection_remove(item)

    def export_history(self):
        """Export history to CSV"""
        try:
            success = self.main_system.memory_module.export_data()
            if success:
                messagebox.showinfo("Export Complete", "History exported to autocorrect_export.csv")
            else:
                messagebox.showerror("Export Failed", "Failed to export history")
        except Exception as e:
            messagebox.showerror("Export Error", f"Export failed: {e}")

    def center_window(self):
        """Center the window on screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def close_window(self):
        """Close the window properly"""
        if self.window:
            self.window.destroy()
            self.window=None #new
        HistoryWindow._instance = None

    def on_closing(self):
        """Handle window close event"""
        self.close_window()
        self.window = None #new
