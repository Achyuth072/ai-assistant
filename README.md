# AI Assistant

A desktop AI Assistant application built with Python and CustomTkinter, designed to provide chat capabilities and various utility functions.

## Setup Instructions

Follow these steps to set up and run the AI Assistant on your local machine.

### Prerequisites

* **Python 3.x:** Ensure you have Python 3 installed. You can download it from [python.org](https://www.python.org/downloads/).

### Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/ai-assistant.git
    cd ai-assistant
    ```

    (Note: Replace `https://github.com/your-username/ai-assistant.git` with the actual repository URL if available.)

2. **Install dependencies:**
    Navigate to the project's root directory and install the required Python packages using pip:

    ```bash
    pip install -r requirements.txt
    ```

### API Key Configuration

This application uses the Google Gemini API. You need to obtain an API key and configure it:

1. **Get a Gemini API Key:**
    * Go to the [Google AI Studio](https://aistudio.google.com/app/apikey) and create a new API key.

2. **Create `config.py`:**
    In the root directory of the project, create a new file named `config.py`.

3. **Add your API Key:**
    Open `config.py` and add the following line, replacing `"YOUR_GEMINI_API_KEY"` with your actual API key:

    ```python
    GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
    ```

## Running the Application

Once you have completed the setup, you can run the application:

```bash
python main.py
```

This will launch the AI Assistant GUI.
