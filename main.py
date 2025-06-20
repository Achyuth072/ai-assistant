# main.py
# type: ignore
import google.generativeai as genai
from config import GEMINI_API_KEY
import assistant_functions
import customtkinter as ctk
import tkinter as tk

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

class AIAssistantGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("AI Assistant")
        self.geometry("800x600")
        
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create chat frame
        self.chat_frame = ctk.CTkFrame(self)
        self.chat_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsew")
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_rowconfigure(0, weight=1)

        # Create chat display
        self.chat_display = ctk.CTkTextbox(self.chat_frame, wrap="word")
        self.chat_display.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.chat_display.configure(state="disabled")

        # Create input frame
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        # Create input field
        self.input_field = ctk.CTkEntry(self.input_frame, placeholder_text="Type your message here...")
        self.input_field.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        self.input_field.bind("<Return>", lambda event: self.send_message())

        # Create send button
        self.send_button = ctk.CTkButton(self.input_frame, text="Send", command=self.send_message)
        self.send_button.grid(row=0, column=1, padx=(5, 10), pady=10)

        # Create appearance mode button
        self.appearance_button = ctk.CTkButton(
            self.input_frame, 
            text="Toggle Theme", 
            command=self.toggle_appearance_mode,
            width=100
        )
        self.appearance_button.grid(row=0, column=2, padx=(5, 10), pady=10)

        # Initialize AI model
        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            tools=tools
        )
        self.chat = self.model.start_chat(enable_automatic_function_calling=True)

        # Display welcome message
        self.append_to_chat("Assistant", "Welcome! I am your personal AI Assistant. How can I help you today?")

    def append_to_chat(self, sender, message):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"{sender}: {message}\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def send_message(self):
        user_input = self.input_field.get().strip()
        if not user_input:
            return

        # Clear input field
        self.input_field.delete(0, "end")

        # Display user message
        self.append_to_chat("You", user_input)

        # Get AI response
        try:
            response = self.chat.send_message(user_input)
            self.append_to_chat("Assistant", response.text)
        except Exception as e:
            self.append_to_chat("System", f"Error: {str(e)}")

    def toggle_appearance_mode(self):
        current_mode = ctk.get_appearance_mode()
        new_mode = "Light" if current_mode == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)

if __name__ == "__main__":
    # Set initial appearance
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    # Create and run app
    app = AIAssistantGUI()
    app.mainloop()