# AI Assistant

A desktop AI Assistant application built with Python and CustomTkinter, designed to provide chat capabilities and various utility functions.

## Setup Instructions

Follow these steps to set up and run the AI Assistant on your Mac or Windows machine.

### Prerequisites

#### For All Users

* **Python 3.x**
* **Git**

#### Mac Users

1. **Install Python**:
   * Open Terminal (press ⌘ + Space, type "Terminal", then press Enter)
   * Install Homebrew (if you don't have it):

     ```bash
     /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
     ```

   * Install Python:

     ```bash
     brew install python
     ```

   * Verify installation:

     ```bash
     python3 --version
     ```

2. **Install Git**:
   * If you installed Homebrew, run:

     ```bash
     brew install git
     ```

   * Alternatively, download from [git-scm.com](https://git-scm.com/download/mac)

#### Windows Users

1. **Install Python**:
   * Download from [python.org](https://www.python.org/downloads/)
   * During installation, check "Add Python to PATH"

2. **Install Git**:
   * Download Git for Windows from [git-scm.com](https://git-scm.com/download/win)
   * Run the installer with default options
   * Verify installation by running in Command Prompt:

     ```bash
     git --version
     ```

### 📥 Installation

1. **Get the Code**:
   * Open Terminal (Mac) or Command Prompt (Windows)
   * Copy the code to your computer:

     ```bash
     git clone https://github.com/your-username/ai-assistant.git
     ```

   * Move into the project folder:

     ```bash
     cd ai-assistant
     ```

2. **Install Required Components**:

   ```bash
   pip install -r requirements.txt
   ```

### 🔑 API Key Setup

Our app uses Google's Gemini AI. Here's how to set it up:

1. **Get Your Free API Key**:
   * Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
   * Click "Create API Key" (you'll need a Google account)

2. **Configure Your Key**:
   * In the project folder, create a new file called `config.py`
   * Open it and add this line (replace the text with your actual key):

     ```python
     GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
     ```

## 🏃 Running the App

Start the AI Assistant with this simple command:

```bash
python main.py
```
