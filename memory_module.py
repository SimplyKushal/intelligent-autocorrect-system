"""
Memory Module - Handles personalization, learning, and correction history
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import csv

class MemoryModule:
    def __init__(self, db_path: str = "autocorrect_memory.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Initialize database
        self.init_database()
        
        # Cache for frequently accessed data
        self.correction_cache = {}
        self.user_preferences_cache = None
        self.ignored_words_cache = set()
        
        # Load caches
        self.refresh_caches()
    
    def init_database(self):
        """Initialize SQLite database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Corrections history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS corrections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        original_text TEXT NOT NULL,
                        corrected_text TEXT NOT NULL,
                        correction_type TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        application TEXT,
                        context TEXT,
                        user_accepted BOOLEAN DEFAULT TRUE
                    )
                ''')
                
                # Personal corrections table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS personal_corrections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        original_text TEXT UNIQUE NOT NULL,
                        corrected_text TEXT NOT NULL,
                        frequency INTEGER DEFAULT 1,
                        last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
                        created_date DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # User preferences table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_date DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Ignored words table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ignored_words (
                        word TEXT PRIMARY KEY,
                        added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        reason TEXT
                    )
                ''')
                
                # Statistics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS statistics (
                        date DATE PRIMARY KEY,
                        corrections_made INTEGER DEFAULT 0,
                        words_processed INTEGER DEFAULT 0,
                        accuracy_score REAL DEFAULT 0.0,
                        typing_speed REAL DEFAULT 0.0
                    )
                ''')
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise
    
    def log_correction(self, original: str, corrected: str, correction_type: str, 
                      confidence: float, application: str = None, context: str = None):
        """Log a correction that was made"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO corrections 
                    (original_text, corrected_text, correction_type, confidence, application, context)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (original, corrected, correction_type, confidence, application, context))
                conn.commit()
                
                # Update statistics
                self.update_daily_stats('corrections_made', 1)
                
        except Exception as e:
            self.logger.error(f"Failed to log correction: {e}")
    
    def add_personal_correction(self, original: str, corrected: str):
        """Add or update a personal correction preference"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO personal_corrections 
                    (original_text, corrected_text, frequency, last_used)
                    VALUES (?, ?, 
                        COALESCE((SELECT frequency + 1 FROM personal_corrections WHERE original_text = ?), 1),
                        CURRENT_TIMESTAMP)
                ''', (original, corrected, original))
                conn.commit()
                
                # Update cache
                self.correction_cache[original.lower()] = corrected
                
                self.logger.info(f"Added personal correction: {original} -> {corrected}")
                
        except Exception as e:
            self.logger.error(f"Failed to add personal correction: {e}")
    
    def get_personal_correction(self, word: str) -> Optional[str]:
        """Get personal correction for a word"""
        word_lower = word.lower()
        
        # Check cache first
        if word_lower in self.correction_cache:
            return self.correction_cache[word_lower]
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT corrected_text FROM personal_corrections 
                    WHERE original_text = ? COLLATE NOCASE
                ''', (word,))
                
                result = cursor.fetchone()
                if result:
                    correction = result[0]
                    self.correction_cache[word_lower] = correction
                    return correction
                
        except Exception as e:
            self.logger.error(f"Failed to get personal correction: {e}")
        
        return None
    
    def add_ignored_word(self, word: str, reason: str = "User choice"):
        """Add word to ignore list"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO ignored_words (word, reason)
                    VALUES (?, ?)
                ''', (word.lower(), reason))
                conn.commit()
                
                # Update cache
                self.ignored_words_cache.add(word.lower())
                
                self.logger.info(f"Added ignored word: {word}")
                
        except Exception as e:
            self.logger.error(f"Failed to add ignored word: {e}")
    
    def is_word_ignored(self, word: str) -> bool:
        """Check if word should be ignored"""
        return word.lower() in self.ignored_words_cache
    
    def get_user_preferences(self) -> Dict:
        """Get user preferences"""
        if self.user_preferences_cache is not None:
            return self.user_preferences_cache
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT key, value FROM user_preferences')
                
                preferences = {}
                for key, value in cursor.fetchall():
                    try:
                        # Try to parse as JSON
                        preferences[key] = json.loads(value)
                    except json.JSONDecodeError:
                        # Store as string if not JSON
                        preferences[key] = value
                
                self.user_preferences_cache = preferences
                return preferences
                
        except Exception as e:
            self.logger.error(f"Failed to get user preferences: {e}")
            return {}
    
    def set_user_preference(self, key: str, value):
        """Set a user preference"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Convert value to JSON string
                value_str = json.dumps(value) if not isinstance(value, str) else value
                
                cursor.execute('''
                    INSERT OR REPLACE INTO user_preferences (key, value, updated_date)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (key, value_str))
                conn.commit()
                
                # Update cache
                if self.user_preferences_cache is not None:
                    self.user_preferences_cache[key] = value
                
        except Exception as e:
            self.logger.error(f"Failed to set user preference: {e}")
    
    def get_correction_history(self, limit: int = 100) -> List[Dict]:
        """Get recent correction history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT original_text, corrected_text, correction_type, confidence, 
                           timestamp, application, context
                    FROM corrections 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
                
                history = []
                for row in cursor.fetchall():
                    history.append({
                        'original': row[0],
                        'corrected': row[1],
                        'type': row[2],
                        'confidence': row[3],
                        'timestamp': row[4],
                        'application': row[5],
                        'context': row[6]
                    })
                
                return history
                
        except Exception as e:
            self.logger.error(f"Failed to get correction history: {e}")
            return []
    
    def get_statistics(self, days: int = 30) -> Dict:
        """Get usage statistics for the last N days"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get date range
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=days)
                
                cursor.execute('''
                    SELECT 
                        SUM(corrections_made) as total_corrections,
                        SUM(words_processed) as total_words,
                        AVG(accuracy_score) as avg_accuracy,
                        AVG(typing_speed) as avg_typing_speed,
                        COUNT(*) as active_days
                    FROM statistics 
                    WHERE date BETWEEN ? AND ?
                ''', (start_date, end_date))
                
                result = cursor.fetchone()
                
                if result:
                    return {
                        'total_corrections': result[0] or 0,
                        'total_words': result[1] or 0,
                        'average_accuracy': result[2] or 0.0,
                        'average_typing_speed': result[3] or 0.0,
                        'active_days': result[4] or 0,
                        'period_days': days
                    }
                
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
        
        return {
            'total_corrections': 0,
            'total_words': 0,
            'average_accuracy': 0.0,
            'average_typing_speed': 0.0,
            'active_days': 0,
            'period_days': days
        }
    
    def update_daily_stats(self, metric: str, value: float):
        """Update daily statistics"""
        try:
            today = datetime.now().date()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert or update today's stats
                cursor.execute(f'''
                    INSERT OR REPLACE INTO statistics (date, {metric})
                    VALUES (?, COALESCE((SELECT {metric} FROM statistics WHERE date = ?), 0) + ?)
                ''', (today, today, value))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to update daily stats: {e}")
    
    def export_data(self, export_path: str = "autocorrect_export.csv"):
        """Export correction data to CSV"""
        try:
            history = self.get_correction_history(limit=10000)
            
            with open(export_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'original', 'corrected', 'type', 'confidence', 'application', 'context']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for entry in history:
                    writer.writerow({
                        'timestamp': entry['timestamp'],
                        'original': entry['original'],
                        'corrected': entry['corrected'],
                        'type': entry['type'],
                        'confidence': entry['confidence'],
                        'application': entry['application'] or '',
                        'context': entry['context'] or ''
                    })
            
            self.logger.info(f"Data exported to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export data: {e}")
            return False
    
    def refresh_caches(self):
        """Refresh internal caches"""
        try:
            # Refresh correction cache
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT original_text, corrected_text FROM personal_corrections')
                
                self.correction_cache = {}
                for original, corrected in cursor.fetchall():
                    self.correction_cache[original.lower()] = corrected
                
                # Refresh ignored words cache
                cursor.execute('SELECT word FROM ignored_words')
                self.ignored_words_cache = {row[0] for row in cursor.fetchall()}
                
                # Clear user preferences cache to force reload
                self.user_preferences_cache = None
                
        except Exception as e:
            self.logger.error(f"Failed to refresh caches: {e}")
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old correction history"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM corrections 
                    WHERE timestamp < ? AND user_accepted = TRUE
                ''', (cutoff_date,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                self.logger.info(f"Cleaned up {deleted_count} old correction records")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
