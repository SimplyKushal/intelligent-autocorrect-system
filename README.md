# Intelligent Autocorrect System

A privacy-first, offline intelligent autocorrect and text enhancement system for Windows. This desktop application provides real-time text correction and rephrasing across all applications, similar to mobile keyboards like Gboard, but optimized for desktop environments with complete privacy protection.

## 🌟 Features

### Core Functionality
- **System-wide Text Correction**: Works across all Windows applications (Notepad, VSCode, browsers, etc.)
- **Real-time Processing**: Instant corrections as you type
- **ML-Driven Suggestions**: Uses lightweight transformer models for intelligent corrections
- **Seamless Integration**: No shortcuts or approval prompts - corrections happen inline
- **Complete Privacy**: 100% offline operation, no cloud APIs or data transmission

### Intelligence & Learning
- **Personalized Learning**: Adapts to your writing style and preferences
- **Context-Aware Corrections**: Considers surrounding text for better suggestions
- **Tone & Formality Control**: Adjustable writing style (casual, neutral, formal)
- **Memory Module**: Remembers your corrections and preferences
- **Multi-layered Processing**: Rule-based, ML-based, and personalized corrections

### User Experience
- **System Tray Integration**: Minimal, non-intrusive interface
- **Configurable Settings**: Extensive customization options
- **Statistics & History**: Track your typing improvements
- **Export Capabilities**: Export your data and corrections
- **Cross-Application Support**: Works in text editors, browsers, office apps, and more

## 🚀 Quick Start

### Prerequisites
- Windows 10/11
- Python 3.8 or higher
- Administrator privileges (for system-wide keyboard hooks)

### Installation

1. **Clone or download** this repository
2. **Run the installer**:
   \`\`\`bash
   python install.py
   \`\`\`
3. **Start the application**:
   \`\`\`bash
   python main.py
   \`\`\`

The application will start in the system tray. Look for the "A" icon in your system tray.

### First Run Setup
1. Right-click the system tray icon
2. Select "Configuration" to customize settings
3. Choose your preferred tone and formality levels
4. Enable/disable correction types as needed
5. Start typing in any application to see corrections in action!

## 🛠️ Configuration

### General Settings
- **Auto-start with Windows**: Automatically start when Windows boots
- **Default tone**: Casual, neutral, or formal writing style
- **Default formality**: Low, medium, or high formality level

### Correction Types
- **Spelling corrections**: Fix common misspellings
- **Grammar corrections**: Basic grammar improvements
- **Style improvements**: Enhance writing style and clarity
- **ML-based corrections**: Use AI models for advanced suggestions

### Personalization
- **Learn from corrections**: Adapt to your preferences over time
- **Personal dictionary**: Add custom word corrections
- **Ignored words**: Skip correction for specific words

## 🧠 How It Works

### Architecture Overview
\`\`\`
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Keyboard Monitor│───▶│  Text Processor  │───▶│  Text Injector  │
│   (pynput)      │    │ (ML + Rules)     │    │  (pyautogui)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Memory Module   │    │ ML Engine        │    │ System Tray UI  │
│  (SQLite)       │    │ (Transformers)   │    │   (pystray)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
\`\`\`

### Processing Pipeline
1. **Input Capture**: Monitor keyboard input across all applications
2. **Word Detection**: Identify word boundaries and context
3. **Multi-layer Processing**:
   - Personal corrections (highest priority)
   - Common corrections dictionary
   - Rule-based pattern matching
   - ML model suggestions
   - Context-aware rephrasing
4. **Text Injection**: Seamlessly replace text in the active application
5. **Learning**: Store successful corrections for future use

### ML Models
The system uses lightweight transformer models optimized for text correction:
- **Default**: Facebook BART-base (compact, fast)
- **Alternative**: T5-small, DistilBERT
- **Custom**: Train your own models on personal data

## 📊 Statistics & Analytics

Track your typing improvements with detailed statistics:
- **Corrections made**: Daily, weekly, monthly counts
- **Accuracy improvements**: Before/after typing accuracy
- **Most corrected words**: Identify common mistakes
- **Typing patterns**: Analyze your writing habits
- **Application usage**: See where corrections are most helpful

## 🔧 Advanced Features

### Custom ML Models
```python
# Example: Using a custom model
config = {
    'ml_model': 'path/to/your/model',
    'ml_confidence_threshold': 0.8
}
