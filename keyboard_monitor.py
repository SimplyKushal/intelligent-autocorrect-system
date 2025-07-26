"""
Keyboard Monitor - Captures and processes keyboard input system-wide
"""

import time
import threading
import logging
from collections import deque
import re
from pynput import keyboard
from pynput.keyboard import Key, Listener

class KeyboardMonitor:
    def __init__(self, text_callback):
        self.text_callback = text_callback
        self.logger = logging.getLogger(__name__)
        
        # Input buffer and state
        self.current_word = ""
        self.context_buffer = deque(maxlen=50)  # Store last 50 words for context
        self.is_monitoring = False
        self.is_paused = False
        
        # Timing and filtering
        self.last_key_time = 0
        self.typing_speed_threshold = 0.05  # Minimum time between keys
        
        # Word boundary detection
        self.word_separators = {' ', '.', ',', '!', '?', ';', ':', '\n', '\t'}
        self.sentence_enders = {'.', '!', '?'}
        
        # Listener object
        self.listener = None

    def start_monitoring(self):
        """Start keyboard monitoring"""
        self.is_monitoring = True

        if self.listener and self.listener.is_alive():
            self.logger.warning("Keyboard listener already running.")
            return

        try:
            self.listener = Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            )
            self.listener.start()
            self.logger.info("Keyboard monitoring started.")
        except Exception as e:
            self.logger.error(f"Keyboard monitoring error: {e}")

    def stop_monitoring(self):
        """Stop keyboard monitoring"""
        self.is_monitoring = False

        if self.listener and self.listener.is_alive():
            self.listener.stop()
            self.listener.join()
            self.logger.info("Keyboard monitoring stopped.")
            self.listener = None  # Prevent accidental reuse
    
    def pause_monitoring(self):
        """Pause processing without stopping listener"""
        self.is_paused = True
        self.logger.info("Keyboard monitoring paused")
    
    def resume_monitoring(self):
        """Resume processing"""
        self.is_paused = False
        self.logger.info("Keyboard monitoring resumed")
    
    def on_key_press(self, key):
        """Handle key press events"""
        if not self.is_monitoring or self.is_paused:
            return
        
        try:
            current_time = time.time()
            
            # Throttle rapid key presses
            if current_time - self.last_key_time < self.typing_speed_threshold:
                return
            
            self.last_key_time = current_time
            
            # Handle different key types
            if hasattr(key, 'char') and key.char:
                self.handle_character(key.char)
            elif key in self.word_separators or key == Key.space:
                self.handle_word_boundary(' ')
            elif key == Key.enter:
                self.handle_word_boundary('\n')
            elif key == Key.backspace:
                self.handle_backspace()
            elif key == Key.tab:
                self.handle_word_boundary('\t')
                
        except Exception as e:
            self.logger.error(f"Error in key press handler: {e}")

    def on_key_release(self, key):
        try:
            if isinstance(key, Key):  # Modifier keys like shift, ctrl, etc.
                if key in [Key.space, Key.enter, Key.tab]:
                    if self.current_word.strip():
                        self.process_completed_word(self.current_word.strip())
                    self.current_word = ""
            elif hasattr(key, 'char') and key.char and key.char.isprintable():
                self.current_word += key.char
        except Exception as e:
            self.logger.error(f"Error in on_key_release: {e}")

    # def on_key_release(self, key):
    # try:
    #     # Convert key to character if possible
    #     if hasattr(key, 'char') and key.char:
    #         self.current_word += key.char
    #
    #     # Detect word boundary (space, enter, tab, punctuation)
    #     elif key in [Key.space, Key.enter, Key.tab] or str(key).startswith('Key.'):
    #         if self.current_word.strip():
    #             self.logger.debug(f"Completed word: '{self.current_word}'")
    #             self.process_completed_word(self.current_word.strip())
    #         self.current_word = ""
    #
    # except Exception as e:
    #     self.logger.error(f"Error in on_key_release: {e}")

    def process_completed_word(self, word):
        corrected = self.text_processor.process_text(word)
        if corrected and corrected.get("corrected_text"):
            self.logger.debug(f"Correction applied: '{word}' → '{corrected['corrected_text']}'")
            self.text_injector.replace_word(word, corrected['corrected_text'])

    def handle_character(self, char):
        """Process regular character input"""
        if char in self.word_separators:
            self.handle_word_boundary(char)
        else:
            self.current_word += char
    
    def handle_word_boundary(self, separator):
        """Process word completion"""
        if self.current_word.strip():
            # Clean and validate the word
            cleaned_word = self.clean_word(self.current_word)
            
            if self.should_process_word(cleaned_word):
                # Get context for better processing
                context = self.get_current_context()
                
                # Determine trigger type
                trigger_type = self.get_trigger_type(separator)
                
                # Send to text processor
                text_data = {
                    'word': cleaned_word,
                    'context': context,
                    'trigger': trigger_type,
                    'separator': separator
                }
                
                # Call the callback in a separate thread to avoid blocking
                threading.Thread(
                    target=self.text_callback,
                    args=(text_data,),
                    daemon=True
                ).start()
                
                # Add to context buffer
                self.context_buffer.append(cleaned_word)
            
            # Reset current word
            self.current_word = ""
    
    def handle_backspace(self):
        """Handle backspace key"""
        if self.current_word:
            self.current_word = self.current_word[:-1]
    
    def clean_word(self, word):
        """Clean and normalize word"""
        # Remove extra whitespace and normalize
        cleaned = word.strip()
        
        # Remove common punctuation that might be attached
        cleaned = re.sub(r'^[^\w]+|[^\w]+$', '', cleaned)
        
        return cleaned
    
    def should_process_word(self, word):
        """Determine if word should be processed"""
        if not word or len(word) < 2:
            return False
        
        # Skip if all numbers
        if word.isdigit():
            return False
        
        # Skip if contains special characters (might be code, URLs, etc.)
        if re.search(r'[<>{}[\]\\|`~]', word):
            return False
        
        # Skip very long words (likely not real words)
        if len(word) > 30:
            return False
        
        return True
    
    def get_current_context(self):
        """Get current context for better text processing"""
        if not self.context_buffer:
            return ""
        
        # Return last few words as context
        context_words = list(self.context_buffer)[-5:]  # Last 5 words
        return " ".join(context_words)
    
    def get_trigger_type(self, separator):
        """Determine what triggered the word completion"""
        if separator == ' ':
            return 'space'
        elif separator in self.sentence_enders:
            return 'sentence_end'
        elif separator == '\n':
            return 'newline'
        elif separator == '\t':
            return 'tab'
        else:
            return 'punctuation'
    
    def get_typing_stats(self):
        """Get current typing statistics"""
        return {
            'current_word_length': len(self.current_word),
            'context_buffer_size': len(self.context_buffer),
            'is_monitoring': self.is_monitoring,
            'is_paused': self.is_paused
        }
