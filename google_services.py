# google_services.py
# type: ignore
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Define the scopes for the permissions you need.
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",  # Added for managing emails (mark as read/unread, etc.)
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/meetings.space.readonly",
    "https://www.googleapis.com/auth/generative-language.retriever"  # Correct scope for Gemini API
]

def get_google_creds():
    """Handles Google API authentication and token management."""
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds

def generate_gemini_summary(text: str, prompt_type: str = "email", model_name: str = "gemini-2.0-flash") -> str:
    """Generates a concise summary using Google's Gemini API with a specified model and prompt type.
    
    Args:
        text (str): The text content to summarize
        prompt_type (str): Type of summary to generate ('email' or 'market_research')
        model_name (str): Name of the Gemini model to use
    """
    import google.generativeai as genai
    
    # Initialize Gemini client
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    
    # Set up the model
    # Adjust configuration based on prompt type
    generation_config = {
        "temperature": 0.7 if prompt_type == "market_research" else 0.5,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 4096 if prompt_type == "market_research" else 2048,
    }
    
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=generation_config
    )
    
    # Generate summary
    if prompt_type == "market_research":
        prompt = f"""
        Generate a detailed market research summary from the following content. Focus on:
        
        1. Industry Overview:
           - Current market size and growth projections
           - Key market segments and their characteristics
           - Regional market dynamics and trends
        
        2. Competitive Analysis:
           - Major players and their market positions
           - Key competitive advantages and strategies
           - Market share distribution (if available)
        
        3. Consumer Insights:
           - Target customer demographics and behaviors
           - Changing consumer preferences
           - Purchase patterns and decision factors
        
        4. Market Dynamics:
           - Primary growth drivers and opportunities
           - Major challenges and potential threats
           - Regulatory factors or compliance requirements
        
        5. Future Outlook:
           - Emerging trends and innovations
           - Growth opportunities and potential risks
           - Technology impacts and digital transformation
        
        Organize the information clearly and support key findings with data when available.
        
        Content to Analyze:
        {text}
        """
    else:  # email summary
        prompt = f"""
        Generate a concise summary of the following email content:
        - Identify the main topic and key points
        - Extract any action items or requests
        - Note important dates, deadlines, or scheduled events
        - Keep the summary clear and professional
        
        Email Content:
        {text}
        """
    
    response = model.generate_content(prompt)
    return response.text