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

def generate_gemini_summary(text: str, prompt_type: str = "email", model_name: str = None,
                           temperature: float = None) -> str:
    """Generates a concise summary using Google's Gemini API with dynamic configuration.
    
    Args:
        text (str): The text content to summarize
        prompt_type (str): Type of summary to generate ('email', 'market_research', or 'property_analysis')
        model_name (str): Name of the Gemini model to use
        temperature (float, optional): Override default temperature for generation
    """
    import google.generativeai as genai
    from typing import Dict, Any
    
    def clean_and_validate_text(text: str, max_length: int = 30000) -> str:
        """Clean and validate input text."""
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Truncate if too long
        if len(text) > max_length:
            print(f"Warning: Input text truncated from {len(text)} to {max_length} characters")
            text = text[:max_length] + "..."
            
        return text
    
    def get_generation_config(prompt_type: str, temperature: float = None) -> Dict[str, Any]:
        """Get dynamic generation configuration based on content and type."""
        configs = {
            "market_research": {
                "temperature": temperature if temperature is not None else 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 4096,
                "candidate_count": 1
            },
            "property_analysis": {
                "temperature": temperature if temperature is not None else 0.6,
                "top_p": 0.90,
                "top_k": 30,
                "max_output_tokens": 3072,
                "candidate_count": 1
            },
            "email": {
                "temperature": temperature if temperature is not None else 0.5,
                "top_p": 0.85,
                "top_k": 20,
                "max_output_tokens": 2048,
                "candidate_count": 1
            },
            "summarize_article": {
                "temperature": temperature if temperature is not None else 0.5,
                "top_p": 0.85,
                "top_k": 20,
                "max_output_tokens": 2048,
                "candidate_count": 1
            }
        }
        return configs.get(prompt_type, configs["email"])
    
    # Initialize Gemini client with error handling
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Gemini client: {e}")
    
    # Clean and validate input text
    text = clean_and_validate_text(text)
    
    # Set up the model with dynamic configuration
    generation_config = get_generation_config(prompt_type, temperature)
    
    # Select appropriate model based on prompt type
    if model_name is None:
        model_name = "gemini-2.0-flash" if prompt_type == "market_research" else "gemini-2.5-flash"
    
    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config
        )
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Gemini model: {e}")
    
    # Generate summary
    if prompt_type == "property_analysis":
        prompt = f"""
        Analyze the following property data and generate insights focused on:
        
        1. Investment Potential:
           - Key value drivers and potential appreciation factors
           - Rental income potential and market positioning
           - ROI considerations and risk factors
        
        2. Market Context:
           - Local market trends and comparable properties
           - Neighborhood characteristics and development
           - Demographic trends and target renter profile
        
        3. Property Assessment:
           - Overall property condition and features analysis
           - Notable strengths and potential concerns
           - Recommended improvements or upgrades
        
        4. Financial Analysis:
           - Price versus market value assessment
           - Operating cost considerations (maintenance, HOA, etc.)
           - Potential revenue optimization strategies
        
        Property Data to Analyze:
        {text}
        """
    elif prompt_type == "summarize_article":
        prompt = f"""
        Summarize the following article for a market research report, focusing on key data, trends, and insights.

        Article Content:
        {text}
        """
    elif prompt_type == "market_research":
        prompt = f"""
        Synthesize the following market research summaries into a single, cohesive analysis. Structure the output for maximum readability using hierarchical indentation for main points, sub-points, and any sub-sub-points. Identify the main trends, challenges, and opportunities with clear headings.

        Summaries to Synthesize:
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
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        raise RuntimeError(f"Failed to generate summary: {e}")