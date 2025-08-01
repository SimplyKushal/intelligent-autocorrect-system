"""
Text Processor - ML-driven text correction and rephrasing engine
"""

import re
import logging
import json
from typing import Dict, List, Optional, Tuple
import sqlite3
from datetime import datetime
import difflib

# For ML capabilities - using lightweight approaches
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logging.warning("Transformers not available. Using rule-based corrections only.")

class TextProcessor:
    def __init__(self, memory_module, config):
        self.memory_module = memory_module
        self.config = config
        self.logger = logging.getLogger("text_processor")
        self.logger.propagate = True

        # Initialize correction engines
        self.rule_engine = RuleBasedCorrector()
        self.ml_engine = None
        
        # Load ML model if available and enabled
        if HAS_TRANSFORMERS and config.get('use_ml_corrections', True):
            self.initialize_ml_engine()
        
        # Common corrections dictionary
        self.common_corrections = self.load_common_corrections()
        
        # Personalization data
        self.user_preferences = self.memory_module.get_user_preferences()
        
    def initialize_ml_engine(self):
        """Initialize ML-based correction engine"""
        try:
            self.logger.info("Initializing ML correction engine...")
            
            # Use a lightweight model for text correction
            model_name = self.config.get('ml_model', 'facebook/bart-base')
            
            # Initialize the model (this might take a moment on first run)
            self.ml_engine = MLCorrector(model_name)
            
            self.logger.info("ML engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ML engine: {e}")
            self.ml_engine = None
        self.logger.debug("Entered process_text() — debug logging is active")


    def process_text(self, word: str, context: str = "", tone: str = "neutral",
                    formality: str = "medium") -> Optional[Dict]:
        result = self.ml_engine.correct(word, context, tone, formality)
        if result:
            self.logger.debug(f"ML corrected '{word}' → '{result['corrected_text']}'")
        else:
            self.logger.debug(f"ML returned no correction for '{word}'")
        return result
        #self.logger.debug(f"Processing word: {word} | Context: '{context}'")
        """
        Process text for corrections and improvements
        
        Args:
            word: The word to process
            context: Surrounding text context
            tone: Desired tone (casual, neutral, formal)
            formality: Formality level (low, medium, high)
            
        Returns:
            Dictionary with correction results or None
        """
        try:
            # Check if word should be skipped
            if self.should_skip_word(word):
                return None
            
            # Try different correction methods in order of preference
            result = None
            
            # 1. Check user's personal corrections first
            result = self.check_personal_corrections(word)
            if result:
                result['source'] = 'personal'
                return result
            
            # 2. Check common corrections
            result = self.check_common_corrections(word)
            if result:
                result['source'] = 'common'
                return result
            
            # 3. Apply rule-based corrections
            result = self.rule_engine.correct(word, context)
            if result:
                result['source'] = 'rules'
                return result
            
            # 4. Try ML-based corrections if available
            if self.ml_engine and len(word) > 3:
                result = self.ml_engine.correct(word, context, tone, formality)
                if result:
                    result['source'] = 'ml'
                    return result
            
            # 5. Check for rephrasing opportunities
            if len(context) > 10:  # Only rephrase with sufficient context
                result = self.suggest_rephrase(word, context, tone, formality)
                if result:
                    result['source'] = 'rephrase'
                    return result
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error processing text '{word}': {e}")
            return None
    
    def should_skip_word(self, word: str) -> bool:
        """Determine if word should be skipped"""
        # Skip very short words
        if len(word) < 2:
            return True
        
        # Skip if all uppercase (might be acronym)
        if word.isupper() and len(word) > 1:
            return True
        
        # Skip if contains numbers and letters (might be code/ID)
        if re.search(r'\d', word) and re.search(r'[a-zA-Z]', word):
            return True
        
        # Skip if user has marked this word to ignore
        if self.memory_module.is_word_ignored(word):
            return True
        
        return False
    
    def check_personal_corrections(self, word: str) -> Optional[Dict]:
        """Check user's personal correction preferences"""
        correction = self.memory_module.get_personal_correction(word)
        if correction:
            return {
                'corrected_text': correction,
                'confidence': 1.0,
                'type': 'personal',
                'reason': 'User preference'
            }
        return None
    
    def check_common_corrections(self, word: str) -> Optional[Dict]:
        """Check against common corrections dictionary"""
        word_lower = word.lower()
        if word_lower in self.common_corrections:
            corrected = self.common_corrections[word_lower]
            
            # Preserve original case
            if word.isupper():
                corrected = corrected.upper()
            elif word.istitle():
                corrected = corrected.title()
            
            return {
                'corrected_text': corrected,
                'confidence': 0.7,
                'type': 'spelling',
                'reason': 'Common misspelling'
            }
        return None
    
    def suggest_rephrase(self, word: str, context: str, tone: str, formality: str) -> Optional[Dict]:
        """Suggest rephrasing based on tone and formality"""
        # This is a simplified version - in a full implementation,
        # this would use more sophisticated NLP
        
        phrase = f"{context} {word}".strip()
        
        # Simple tone adjustments
        if tone == 'formal' and formality == 'high':
            replacements = {
                'gonna': 'going to',
                'wanna': 'want to',
                'gotta': 'have to',
                'kinda': 'kind of',
                'sorta': 'sort of'
            }
            
            for informal, formal in replacements.items():
                if informal in phrase.lower():
                    new_phrase = phrase.lower().replace(informal, formal)
                    return {
                        'corrected_text': formal if word.lower() == informal else word,
                        'confidence': 0.7,
                        'type': 'formality',
                        'reason': f'Formalized for {tone} tone'
                    }
        
        return None
    
    def load_common_corrections(self) -> Dict[str, str]:
        """Load common spelling corrections"""
        # This would typically load from a file or database
        # Here's a small sample
        return {
            'teh': 'the',
            'adn': 'and',
            'recieve': 'receive',
            'seperate': 'separate',
            'definately': 'definitely',
            'occured': 'occurred',
            'accomodate': 'accommodate',
            'begining': 'beginning',
            'beleive': 'believe',
            'calender': 'calendar',
            'cemetary': 'cemetery',
            'changable': 'changeable',
            'collegue': 'colleague',
            'concious': 'conscious',
            'dilemna': 'dilemma',
            'embarass': 'embarrass',
            'enviroment': 'environment',
            'existance': 'existence',
            'foriegn': 'foreign',
            'goverment': 'government',
            'harrass': 'harass',
            'independant': 'independent',
            'judgement': 'judgment',
            'knowlege': 'knowledge',
            'liason': 'liaison',
            'maintainance': 'maintenance',
            'neccessary': 'necessary',
            'occassion': 'occasion',
            'persistant': 'persistent',
            'priviledge': 'privilege',
            'questionaire': 'questionnaire',
            'recomend': 'recommend',
            'succesful': 'successful',
            'tommorrow': 'tomorrow',
            'untill': 'until',
            'vaccuum': 'vacuum',
            'wierd': 'weird'
        }
    
    def update_config(self, new_config):
        """Update processor configuration"""
        self.config.update(new_config)
        
        # Reinitialize ML engine if settings changed
        if HAS_TRANSFORMERS and new_config.get('use_ml_corrections', True):
            if not self.ml_engine:
                self.initialize_ml_engine()

class RuleBasedCorrector:
    """Rule-based text correction engine"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Common patterns and their corrections
        self.patterns = [
            # Double letters that should be single
            (r'(.)\1{2,}', r'\1\1'),  # More than 2 consecutive letters -> 2
            
            # Common letter swaps
            (r'ie(?=d|s|r)', 'ei'),  # ie -> ei in certain contexts
            (r'recieve', 'receive'),
            (r'beleive', 'believe'),
            
            # Common endings
            (r'ise$', 'ize'),  # British to American spelling
            (r'colour', 'color'),
            (r'favour', 'favor'),
            
            # Capitalization after periods
            (r'(\. )([a-z])', lambda m: m.group(1) + m.group(2).upper()),
        ]
    
    def correct(self, word: str, context: str = "") -> Optional[Dict]:
        """Apply rule-based corrections"""
        original_word = word
        
        for pattern, replacement in self.patterns:
            if isinstance(replacement, str):
                new_word = re.sub(pattern, replacement, word, flags=re.IGNORECASE)
            else:
                new_word = re.sub(pattern, replacement, word)
            
            if new_word != word:
                return {
                    'corrected_text': new_word,
                    'confidence': 0.8,
                    'type': 'pattern',
                    'reason': f'Applied pattern rule'
                }
        
        return None

class MLCorrector:
    """ML-based text correction using transformers"""
    
    def __init__(self, model_name: str):
        self.logger = logging.getLogger(f"text_processor")
        self.logger.setLevel(logging.DEBUG)
        self.model_name = model_name
        
        try:
            # Initialize the model for text correction
            self.corrector = pipeline(
                "text2text-generation",
                model=model_name,
                tokenizer=model_name,
                max_length=50,
                device=-1  # Use CPU
            )
            
        except Exception as e:
            self.logger.error(f"Failed to load ML model: {e}")
            self.corrector = None
    
    def correct(self, word: str, context: str = "", tone: str = "neutral", 
               formality: str = "medium") -> Optional[Dict]:
        """Apply ML-based corrections"""
        self.logger.debug("MLCorrector.active - ready to process")
        if not self.corrector:
            return None
        
        try:
            # Create prompt for correction
            if context:
                prompt = f"Correct this text: {context} {word}"
            else:
                prompt = f"Correct this word: {word}"
            
            # Generate correction
            result = self.corrector(prompt, max_length=30, num_return_sequences=1)
            
            if result and len(result) > 0:
                corrected_text = result[0]['generated_text'].strip()
                
                # Extract just the corrected word if possible
                corrected_word = self.extract_corrected_word(word, corrected_text)

                if corrected_word and corrected_word != word:
                    return {
                        'corrected_text': corrected_word,
                        'confidence': 0.75,
                        'type': 'ml',
                        'reason': 'ML model suggestion'
                    }
            
        except Exception as e:
            self.logger.error(f"ML correction failed: {e}")
        
        return None
    
    def extract_corrected_word(self, original: str, corrected_text: str) -> str:
        """Extract the corrected word from ML output"""
        # Simple extraction - in practice, this would be more sophisticated
        words = corrected_text.split()
        
        # Find the word most similar to original
        best_match = original
        best_ratio = 0
        
        for word in words:
            ratio = difflib.SequenceMatcher(None, original.lower(), word.lower()).ratio()
            if ratio > best_ratio and ratio > 0.5:
                best_ratio = ratio
                best_match = word
        
        return best_match
