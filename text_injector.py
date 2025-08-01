"""
Text Injector - Handles seamless text replacement in active applications
"""

import time
import logging
import pyautogui
import pyperclip
from pynput.keyboard import Key, Controller
import win32gui_struct
import win32gui
import win32con
import win32clipboard

class TextInjector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.keyboard = Controller()
        
        # Configure pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.01  # Small delay between actions
        
        # Injection methods in order of preference
        self.injection_methods = [
            self.inject_via_clipboard,
            self.inject_via_keyboard,
            self.inject_via_sendkeys
        ]
    
    def replace_text(self, original_text: str, new_text: str) -> bool:
        """
        Replace text in the currently active application
        
        Args:
            original_text: Text to replace
            new_text: Replacement text
            
        Returns:
            True if replacement was successful
        """
        try:
            # Get active window info
            active_window = self.get_active_window_info()

            # Choose injection method based on application
            method = self.choose_injection_method(active_window)

            # Fallback delete+type strategy if the injection method fails or is None
            if method is None:
                self.logger.warning(f"No injection method found for app: {active_window['class_name']}")
                return self.fallback_typing(original_text, new_text)

            # Perform the replacement
            success = method(original_text, new_text)

            if not success:
                self.logger.warning(f"Method '{method.__name__}' failed — falling back to keyboard erase")
                success = self.fallback_typing(original_text, new_text)

            if success:
                self.logger.debug(f"Successfully replaced '{original_text}' with '{new_text}'")
            else:
                self.logger.warning(f"Failed to replace '{original_text}' with '{new_text}'")

            return success

        except Exception as e:
            self.logger.error(f"Text injection failed: {e}")
            return False

        # try:
        #     # Get active window info
        #     active_window = self.get_active_window_info()
        #
        #     # Choose injection method based on application
        #     method = self.choose_injection_method(active_window)
        #
        #     # Perform the replacement
        #     success = method(original_text, new_text)
        #
        #     if success:
        #         self.logger.debug(f"Successfully replaced '{original_text}' with '{new_text}'")
        #     else:
        #         self.logger.warning(f"Failed to replace '{original_text}' with '{new_text}'")
        #
        #     return success
        #
        # except Exception as e:
        #     self.logger.error(f"Text injection failed: {e}")
        #     return False
    
    def get_active_window_info(self) -> dict:
        """Get information about the currently active window"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            window_text = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)

            # hwnd = win32gui_struct.GetForegroundWindow()
            # window_text = win32gui_struct.GetWindowText(hwnd)
            # class_name = win32gui_struct.GetClassName(hwnd)
            
            return {
                'hwnd': hwnd,
                'title': window_text,
                'class': class_name
            }
        except Exception as e:
            self.logger.error(f"Failed to get active window info: {e}")
            return {}

    def fallback_typing(self, original_text, new_text):
        """Delete old word character-by-character and type the corrected one"""
        try:
            for _ in range(len(original_text)):
                self.keyboard.press(Key.backspace)
                self.keyboard.release(Key.backspace)
                time.sleep(0.01)  # slight delay between keystrokes

            self.keyboard.type(new_text)
            self.logger.info(f"Fallback typed: '{new_text}'")
            return True

        except Exception as e:
            self.logger.error(f"Fallback typing failed: {e}")
            return False

    def choose_injection_method(self, window_info: dict):
        """Choose the best injection method for the current application"""
        class_name = window_info.get('class', '').lower()
        title = window_info.get('title', '').lower()
        
        # Special handling for certain applications
        if 'notepad' in title or 'notepad' in class_name:
            return self.inject_via_clipboard
        elif 'code' in title or 'visual studio' in title:
            return self.inject_via_keyboard
        elif 'chrome' in title or 'firefox' in title or 'edge' in title:
            return self.inject_via_clipboard
        else:
            # Default to clipboard method
            return self.inject_via_clipboard
    
    def inject_via_clipboard(self, original_text: str, new_text: str) -> bool:
        """Inject text using clipboard copy/paste method"""
        try:
            # Store current clipboard content
            original_clipboard = self.get_clipboard_text()
            
            # Select the word to replace
            if not self.select_word(original_text):
                return False
            
            # Copy new text to clipboard
            pyperclip.copy(new_text)
            time.sleep(0.05)  # Small delay
            
            # Paste the new text
            self.keyboard.press(Key.ctrl)
            self.keyboard.press('v')
            self.keyboard.release('v')
            self.keyboard.release(Key.ctrl)
            
            time.sleep(0.05)
            
            # Restore original clipboard content
            if original_clipboard:
                pyperclip.copy(original_clipboard)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Clipboard injection failed: {e}")
            return False
    
    def inject_via_keyboard(self, original_text: str, new_text: str) -> bool:
        """Inject text using keyboard simulation"""
        try:
            # Select the word to replace
            if not self.select_word(original_text):
                return False
            
            # Type the new text
            for char in new_text:
                self.keyboard.type(char)
                time.sleep(0.01)  # Small delay between characters
            
            return True
            
        except Exception as e:
            self.logger.error(f"Keyboard injection failed: {e}")
            return False
    
    def inject_via_sendkeys(self, original_text: str, new_text: str) -> bool:
        """Inject text using Windows SendKeys"""
        try:
            import win32api
            
            # Select the word to replace
            if not self.select_word(original_text):
                return False
            
            # Send the new text
            for char in new_text:
                win32api.keybd_event(ord(char.upper()), 0, 0, 0)
                win32api.keybd_event(ord(char.upper()), 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.01)
            
            return True
            
        except Exception as e:
            self.logger.error(f"SendKeys injection failed: {e}")
            return False
    
    def select_word(self, word: str) -> bool:
        """Select the word that was just typed"""
        try:
            # Move cursor to beginning of word
            word_length = len(word)
            
            # Use Ctrl+Shift+Left to select word
            for _ in range(word_length):
                self.keyboard.press(Key.shift)
                self.keyboard.press(Key.left)
                self.keyboard.release(Key.left)
                self.keyboard.release(Key.shift)
                time.sleep(0.01)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Word selection failed: {e}")
            return False
    
    def get_clipboard_text(self) -> str:
        """Get current clipboard text content"""
        try:
            return pyperclip.paste()
        except Exception:
            return ""
    
    def test_injection(self) -> bool:
        """Test if text injection is working"""
        try:
            # Simple test - type and immediately replace
            test_word = "testword"
            replacement = "replaced"
            
            # Type test word
            self.keyboard.type(test_word)
            time.sleep(0.1)
            
            # Try to replace it
            success = self.replace_text(test_word, replacement)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Injection test failed: {e}")
            return False
