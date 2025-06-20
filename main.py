# main.py
# type: ignore
import google.generativeai as genai
from config import GEMINI_API_KEY
import assistant_functions

# Configure the API key
genai.configure(api_key=GEMINI_API_KEY)  # type: ignore

# Define the tools the model can use
tools = [
    assistant_functions.set_reminder,
    assistant_functions.send_email,
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
]

# Create the model with the tools
model = genai.GenerativeModel(  # type: ignore
    model_name='gemini-2.5-flash',
    tools=tools
)

# Start the chat
chat = model.start_chat(enable_automatic_function_calling=True)  # type: ignore

print("Welcome! I am your personal AI Assistant. Type 'exit' to quit.")
while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        print("Goodbye!")
        break
    
    # Send the user's message to the chat
    response = chat.send_message(user_input)
    
    # The library automatically handles function calls and returns the final response.
    # Just print the text part of the model's reply.
    print(f"Assistant: {response.text}")