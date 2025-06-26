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

        # Configure window with modern styling
        self.title("AI Assistant")
        self.geometry("1200x700")
        ctk.set_default_color_theme("blue")  # Modern blue theme
        self.configure(fg_color=("#F5F7FA", "#1E1E1E"))  # Light/Dark background
        
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)  # Sidebar fixed width
        self.grid_columnconfigure(1, weight=1)  # Main content area expands
        
        # Create sidebar
        self.sidebar_expanded = True  # Track sidebar state
        self.sidebar_width = 250
        self.sidebar_min_width = 50
        # Create sidebar with animation support
        self.sidebar = ctk.CTkFrame(
            self,
            width=self.sidebar_width,
            fg_color=("white", "#2A2D32"),
            corner_radius=12
        )
        self.sidebar.grid(row=0, column=0, padx=(10, 0), pady=(15, 10), sticky="nsew")  # Added bottom padding
        self.sidebar.grid_propagate(False)  # Maintain width
        
        # Enhanced animation parameters
        self.animation_duration = 70  # Slightly longer for smoother feel
        self.animation_steps = 60  # More steps for smoother animation
        self.animation_running = False
        self.active_button = None  # Track pressed button for visual feedback
        
        # Initialize easing function for smoother animation
        self.sidebar_ease_func = QuadEaseInOut(start=0, end=1, duration=self.animation_steps)
        
        # Initialize button interactions
        self._init_button_interactions()

        # Collapse button
        self.collapse_btn = ctk.CTkButton(
            self.sidebar,
            text="◀",
            width=30,
            height=30,
            command=self.toggle_sidebar,
            fg_color="transparent",
            hover_color=("#EBEBEB", "#3A3F45"),
            corner_radius=8
        )
        self.collapse_btn.grid(row=0, column=0, padx=(self.sidebar_width-40, 5), pady=5, sticky="e")
        
        # Settings section
        self.settings_label = ctk.CTkLabel(
            self.sidebar, 
            text="Settings", 
            font=("Segoe UI", 16, "bold"),
            text_color=("#2B7DE9", "#4DABF7")
        )
        self.settings_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        self.appearance_button = ctk.CTkButton(
            self.sidebar,
            text="Toggle Theme",
            command=self.toggle_appearance_mode,
            fg_color=("#2B7DE9", "#1F5AA8"),
            hover_color=("#2368CC", "#194A8C"),
            font=("Segoe UI", 12),
            height=36,
            corner_radius=8
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
        self.tabview = ctk.CTkTabview(
            self,
            segmented_button_fg_color=("#E9ECEF", "#2D3035"),
            segmented_button_selected_color=("#2B7DE9", "#1F5AA8"),
            segmented_button_selected_hover_color=("#2368CC", "#194A8C"),
            corner_radius=8
        )
        self.tabview.grid(row=0, column=1, padx=10, pady=(0, 10), sticky="nsew")  # Added bottom padding
        
        # Add tabs
        self.chat_tab = self.tabview.add("💬 Chat")
        
        # Configure tab layouts
        self.chat_tab.grid_rowconfigure(0, weight=1)
        self.chat_tab.grid_columnconfigure(0, weight=1)
        
        # Create chat display in chat tab
        self.chat_display = ctk.CTkTextbox(
            self.chat_tab, 
            wrap="word",
            fg_color=("white", "#252526"),
            border_color=("#E9ECEF", "#3A3F45"),
            border_width=1,
            corner_radius=8,
            font=("Segoe UI", 13)
        )
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
            height=45,
            fg_color=("white", "#2D3035"),
            border_color=("#CED4DA", "#3A3F45"),
            border_width=1,
            corner_radius=8,
            font=("Segoe UI", 13)
        )
        self.input_field.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        self.input_field.bind("<Return>", lambda event: self.send_message())

        # Create send button
        self.send_button = ctk.CTkButton(
            self.input_frame,
            text="Send",
            command=lambda: self.send_message(),
            width=100,
            height=45,
            fg_color=("#2B7DE9", "#1F5AA8"),
            hover_color=("#2368CC", "#194A8C"),
            font=("Segoe UI", 13, "bold"),
            corner_radius=8
        )
        self.send_button.grid(row=0, column=1, padx=(5, 10), pady=10)

        # Initialize AI model
        self.model = GenerativeModel(
            model_name='gemini-2.5-flash',
            tools=tools
        )
        self.chat = self.model.start_chat(enable_automatic_function_calling=True)

        # Display welcome message with styled text
        welcome_msg = """
        Welcome to your AI Assistant! ✨

        I'm here to help you with:
        • Answering questions
        • Running tools and automations
        • Analyzing data
        • And much more!

        How can I assist you today?
        """
        self.append_to_chat("Assistant", welcome_msg.strip())
        
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
        
        # Show text-based loading indicator
        self.loading_dots = 1
        self.current_chat.configure(state="normal")
        self.current_chat.insert("end", "Assistant is thinking...")
        self.current_chat.configure(state="disabled")
        self._animate_loading()
        
        # Start async response handling
        self.after(50, lambda: self.get_ai_response(user_input))
    
    def get_ai_response(self, user_input):
        try:
            # Get AI response in a non-blocking way
            response = self.chat.send_message(user_input)
            
            # Remove loading indicator and show response
            self.current_chat.configure(state="normal")
            self.current_chat.delete("end-3l", "end-1l")
            if hasattr(self, 'loading_dots'):
                self.current_chat.delete(self.loading_dots)
            self.current_chat.configure(state="disabled")
            
            self.append_to_chat("Assistant", response.text)
        except Exception as e:
            # Remove loading indicator and show error
            self.current_chat.configure(state="normal")
            self.current_chat.delete("end-3l", "end-1l")
            if hasattr(self, 'loading_dots'):
                self.current_chat.delete(self.loading_dots)
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
    
    def _init_button_interactions(self):
        """Initialize button hover and press effects"""
        self.button_states = {}  # Track button states in a dictionary
        
        # Bind global events
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event):
        """Handle mouse enter events for buttons"""
        widget = event.widget
        if isinstance(widget, ctk.CTkButton):
            if widget != self.active_button:
                self.button_states[id(widget)] = widget.cget("fg_color")
                widget.configure(fg_color=widget.cget("hover_color"))
    def _on_leave(self, event):
        """Handle mouse leave events for buttons"""
        widget = event.widget
        if isinstance(widget, ctk.CTkButton):
            if widget != self.active_button and id(widget) in self.button_states:
                widget.configure(fg_color=self.button_states[id(widget)])
    
    
    def _reset_button(self):
        """Reset button appearance after press"""
        if self.active_button and id(self.active_button) in self.button_states:
            original_color = self.button_states.get(id(self.active_button))
            if original_color:
                self.active_button.configure(fg_color=original_color, hover_color=None)
            self.active_button = None
    
    def _animate_loading(self):
        """Animate loading dots"""
        if not hasattr(self, 'loading_dots'):
            return
            
        self.current_chat.configure(state="normal")
        self.current_chat.delete("end-1l linestart", "end-1c")
        
        dots = "." * self.loading_dots
        self.current_chat.insert("end", f"Assistant is thinking{dots}")
        
        self.loading_dots = self.loading_dots + 1 if self.loading_dots < 3 else 1
        self.current_chat.configure(state="disabled")
        self.after(500, self._animate_loading)