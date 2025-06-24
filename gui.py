import customtkinter as ctk
import tkinter as tk
import time
from typing import List, Callable, Dict
from easing_functions import QuadEaseInOut
from google.generativeai.generative_models import GenerativeModel

class AIAssistantGUI(ctk.CTk):
    """Main GUI class for the AI Assistant application."""
    def __init__(self, tools: List[Callable]):
        """
        Initialize the AI Assistant GUI.
        
        Args:
            tools: List of callable functions that the assistant can use
        """
        super().__init__()
        self.tools = tools  # Store tools as instance variable

        # Configure window
        self.title("AI Assistant")
        self.geometry("1200x700")  # Larger default size for better layout
        
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)  # Main content area expands
        
        # Create sidebar
        self.sidebar_expanded = True  # Track sidebar state
        self.sidebar_width = 250
        self.sidebar_min_width = 50
        # Create sidebar with animation support
        self.sidebar = ctk.CTkFrame(self, width=self.sidebar_width)
        self.sidebar.grid(row=0, column=0, rowspan=2, padx=(10, 0), pady=10, sticky="nsew")
        self.sidebar.grid_propagate(False)  # Maintain width
        
        # Configure animation parameters
        self.animation_duration = 100  # milliseconds - faster transition
        self.animation_steps = 30  # more steps for smoother animation at higher speed
        self.animation_running = False
        
        # Initialize easing function
        self.sidebar_ease_func = QuadEaseInOut(start=0, end=1, duration=self.animation_steps)
        
        # Collapse button
        self.collapse_btn = ctk.CTkButton(
            self.sidebar,
            text="◀",
            width=30,
            command=self.toggle_sidebar
        )
        self.collapse_btn.grid(row=0, column=0, padx=(self.sidebar_width-40, 5), pady=5, sticky="e")
        
        # Settings section
        self.settings_label = ctk.CTkLabel(self.sidebar, text="Settings", font=("default", 16, "bold"))
        self.settings_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        self.appearance_button = ctk.CTkButton(
            self.sidebar,
            text="Toggle Theme",
            command=self.toggle_appearance_mode
        )
        self.appearance_button.grid(row=1, column=0, padx=10, pady=(0, 15), sticky="ew")
        
        # History section
        self.history_label = ctk.CTkLabel(self.sidebar, text="Conversation History", font=("default", 16, "bold"))
        self.history_label.grid(row=2, column=0, padx=10, pady=(15, 5), sticky="w")
        
        # Create read-only history display with placeholder text
        self.history_list = ctk.CTkTextbox(self.sidebar, height=200, state="disabled")
        self.history_list.grid(row=3, column=0, padx=10, pady=(0, 15), sticky="ew")
        
        # Add placeholder text explaining the history feature
        self.history_list.configure(state="normal")
        self.history_list.insert("1.0", "Your conversation history will appear here automatically. This area shows your recent interactions and is read-only.")
        self.history_list.configure(state="disabled")
        
        # Tools section with description
        self.tools_label = ctk.CTkLabel(self.sidebar, text="Quick Access Tools", font=("default", 16, "bold"))
        self.tools_label.grid(row=4, column=0, padx=10, pady=(15, 5), sticky="w")
        
        # Add tools description
        self.tools_desc = ctk.CTkLabel(
            self.sidebar,
            text="Click any tool below to quickly access its functionality without typing commands.",
            wraplength=220,
            justify="left"
        )
        self.tools_desc.grid(row=5, column=0, padx=10, pady=(0, 5), sticky="w")
        
        # Create scrollable tools container
        self.tools_scroll = ctk.CTkScrollableFrame(self.sidebar, height=200)
        self.tools_scroll.grid(row=6, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        # Create tool buttons dynamically in scrollable frame
        for i, tool in enumerate(tools):
            btn = ctk.CTkButton(
                self.tools_scroll,
                text=tool.__name__.replace('_', ' ').title(),
                command=lambda t=tool: self.use_tool(t)
            )
            btn.grid(row=i, column=0, padx=5, pady=2, sticky="ew")

        # Create main content tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=1, padx=10, pady=(10, 0), sticky="nsew", rowspan=2)
        
        # Add tabs
        self.chat_tab = self.tabview.add("💬 Chat")
        
        # Configure tab layouts
        self.chat_tab.grid_rowconfigure(0, weight=1)
        self.chat_tab.grid_columnconfigure(0, weight=1)
        
        # Create chat display in chat tab
        self.chat_display = ctk.CTkTextbox(self.chat_tab, wrap="word")
        self.chat_display.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.chat_display.configure(state="disabled")

        # Set current chat display reference
        self.current_chat = self.chat_display

        # Create input frame in chat tab
        self.input_frame = ctk.CTkFrame(self.chat_tab)
        self.input_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        # Create input field
        self.input_field = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Type your message here...",
            height=40  # Taller input field
        )
        self.input_field.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        self.input_field.bind("<Return>", lambda event: self.send_message())

        # Create send button
        self.send_button = ctk.CTkButton(
            self.input_frame,
            text="Send",
            command=self.send_message,
            width=100,
            height=40  # Match input field height
        )
        self.send_button.grid(row=0, column=1, padx=(5, 10), pady=10)

        # Initialize AI model
        self.model = GenerativeModel(
            model_name='gemini-2.5-flash',
            tools=tools
        )
        self.chat = self.model.start_chat(enable_automatic_function_calling=True)

        # Display welcome message
        self.append_to_chat("Assistant", "Welcome! I am your personal AI Assistant. How can I help you today?")
        
    def append_to_chat(self, sender, message):
        """Appends a message to the current chat display."""
        # Update current chat display
        self.current_chat.configure(state="normal")
        self.current_chat.insert("end", f"{sender}: {message}\n\n")
        self.current_chat.configure(state="disabled")
        self.current_chat.see("end")
        
        # Update history list (keeping last 5 interactions)
        self.history_list.configure(state="normal")
        self.history_list.delete("1.0", "end")  # Clear existing content
        
        # Get last 10 lines from current chat display
        chat_content = self.current_chat.get("1.0", "end").strip().split("\n\n")
        recent_history = chat_content[-5:] if len(chat_content) > 5 else chat_content
        
        if len(recent_history) > 0:
            self.history_list.insert("1.0", "\n\n".join(recent_history))
        else:
            # Show placeholder if no history
            self.history_list.insert("1.0", "Your conversation history will appear here automatically. This area shows your recent interactions and is read-only.")
        
        self.history_list.configure(state="disabled")

    def send_message(self):
        user_input = self.input_field.get().strip()
        if not user_input:
            return

        # Clear input field and disable it while processing
        self.input_field.delete(0, "end")
        self.input_field.configure(state="disabled")
        self.send_button.configure(state="disabled")
        
        # Display user message
        self.append_to_chat("You", user_input)
        
        # Show loading indicator
        self.append_to_chat("Assistant", "Thinking...")
        
        # Start async response handling
        self.after(50, lambda: self.get_ai_response(user_input))
    
    def get_ai_response(self, user_input):
        try:
            # Get AI response in a non-blocking way
            response = self.chat.send_message(user_input)
            
            # Remove loading indicator and show response
            self.current_chat.configure(state="normal")
            self.current_chat.delete("end-3l", "end-1l")  # Remove "Thinking..." line
            self.current_chat.configure(state="disabled")
            
            self.append_to_chat("Assistant", response.text)
        except Exception as e:
            # Remove loading indicator and show error
            self.current_chat.configure(state="normal")
            self.current_chat.delete("end-3l", "end-1l")  # Remove "Thinking..." line
            self.current_chat.configure(state="disabled")
            
            self.append_to_chat("System", f"Error: {str(e)}")
        finally:
            # Re-enable input controls
            self.input_field.configure(state="normal")
            self.send_button.configure(state="normal")
            self.input_field.focus()

    def toggle_appearance_mode(self):
        current_mode = ctk.get_appearance_mode()
        new_mode = "Light" if current_mode == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)
    
    def toggle_sidebar(self):
        """Toggle sidebar expansion state with smooth non-blocking animation"""
        if self.animation_running:
            return
        
        self.animation_running = True
        target_width = self.sidebar_min_width if self.sidebar_expanded else self.sidebar_width
        current_width = self.sidebar_width if self.sidebar_expanded else self.sidebar_min_width
        
        # Store current state before animation
        was_expanded = self.sidebar_expanded
        
        def update_sidebar_state():
            """Update widget states after animation completes"""
            self.sidebar_expanded = not was_expanded
            self.animation_running = False
            self.collapse_btn.configure(text="▶" if not self.sidebar_expanded else "◀")
            
            # Update widget visibility based on final state
            for widget in self.sidebar.winfo_children():
                if widget != self.collapse_btn:
                    try:
                        if not self.sidebar_expanded:
                            widget.grid_remove()  # Fully hide widget when collapsed
                        else:
                            widget.grid()  # Show widget when expanded
                            widget.configure(fg_color=("gray90", "gray20"))
                    except:
                        pass
        
        def animate_step(step=0):
            """Single animation step using easing function"""
            if step >= self.animation_steps:
                update_sidebar_state()
                return
            
            # Calculate current width using easing function
            eased_progress = self.sidebar_ease_func.ease(step)
            interpolated_width = current_width + (target_width - current_width) * eased_progress
            
            # Update sidebar width
            self.sidebar.configure(width=int(interpolated_width))
            
            # Reposition collapse button
            btn_padx = (max(interpolated_width-40, 10), 5)  # More padding when collapsed
            self.collapse_btn.grid(row=0, column=0, padx=btn_padx, pady=5, sticky="e")
            self.collapse_btn.lift()  # Ensure button stays on top
            
            # Schedule next frame
            self.after(int(self.animation_duration / self.animation_steps),
                      lambda: animate_step(step + 1))
        
        # Start animation
        animate_step()
    
    def use_tool(self, tool):
        """Handle tool selection from sidebar with parameter collection dialog"""
        tool_name = tool.__name__.replace('_', ' ').title()
        
        # Create parameter collection dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Use {tool_name}")
        dialog.geometry("450x400")  # Larger size for better layout
        dialog.minsize(400, 350)   # Set minimum size
        dialog.transient(self)     # Make dialog modal
        dialog.grab_set()          # Make dialog take focus
        
        # Add description frame with distinctive styling
        desc_frame = ctk.CTkFrame(dialog, fg_color=("gray90", "gray20"))
        desc_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(desc_frame,
                    text=f"Enter parameters for {tool_name}",
                    font=("default", 14, "bold")).pack(pady=5)
        
        # Create scrollable frame for parameters with fixed height
        params_frame = ctk.CTkScrollableFrame(dialog, height=180)
        params_frame.pack(fill="x", padx=10, pady=5)
        
        param_entries = {}
        for param in tool.__code__.co_varnames[:tool.__code__.co_argcount]:
            param_frame = ctk.CTkFrame(params_frame)
            param_frame.pack(fill="x", pady=2)
            
            # Convert parameter name to title case for display
            param_label = param.replace('_', ' ').title()
            ctk.CTkLabel(param_frame, text=param_label).pack(side="left", padx=5)
            
            entry = ctk.CTkEntry(param_frame)
            entry.pack(side="right", fill="x", expand=True, padx=5)
            param_entries[param] = entry
        
        def submit():
            # Collect parameters
            params = {name: entry.get() for name, entry in param_entries.items()}
            param_str = ", ".join(f"{k}='{v}'" for k, v in params.items())
            
            # Show collection confirmation in chat
            self.append_to_chat("System",
                              f"Collected parameters for {tool_name}:\n" +
                              "\n".join(f"- {k}: {v}" for k, v in params.items()))
            
            try:
                # Execute tool with parameters
                result = tool(**params)
                self.append_to_chat("System", f"Tool result: {result}")
            except Exception as e:
                self.append_to_chat("System", f"Error executing tool: {str(e)}")
            
            dialog.destroy()
        
        # Create button frame at the bottom with clear separation
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(fill="x", side="bottom", padx=10, pady=10)
        
        # Improved submit button with prominent styling
        submit_btn = ctk.CTkButton(
            button_frame,
            text="Submit",
            command=submit,
            width=200,  # Wider for better visibility
            height=45,  # Taller for better touch targets
            font=("default", 14, "bold"),
            fg_color=("#2B7DE9", "#1F5AA8"),  # Distinctive blue shades
            hover_color=("#2368CC", "#194A8C"),
            corner_radius=10
        )
        submit_btn.pack(padx=20, pady=10)
        
        # Force proper layering
        dialog.lift()
        button_frame.lift()
        submit_btn.lift()
        submit_btn.lift()
    
    def _show_error(self, message: str):
        """Display error message in a dialog"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Error")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(
            dialog,
            text=message,
            wraplength=250
        ).pack(padx=20, pady=20)
        
        ctk.CTkButton(
            dialog,
            text="OK",
            command=dialog.destroy
        ).pack(pady=10)
    