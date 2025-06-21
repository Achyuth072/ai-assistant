import google.generativeai as genai
from config import GEMINI_API_KEY
import assistant_functions
import market_research
from gui import AIAssistantGUI

# Configure the API key
genai.configure(api_key=GEMINI_API_KEY)  # type: ignore

# Define the tools the model can use
tools = [
    assistant_functions.set_reminder,
    assistant_functions.send_email,
    assistant_functions.summarize_email_by_query,
    assistant_functions.summarize_email_by_id,
    assistant_functions.list_calendar_events,
    assistant_functions.delete_calendar_event,
    assistant_functions.search_emails,
    assistant_functions.get_unread_emails,
    assistant_functions.add_task,
    assistant_functions.list_tasks,
    assistant_functions.mark_task_complete,
    assistant_functions.delete_task,
    assistant_functions.create_instant_meeting,
    assistant_functions.join_next_meeting,
    market_research.conduct_market_research,
]

if __name__ == "__main__":
    # Create and run app
    app = AIAssistantGUI(tools)
    app.mainloop()