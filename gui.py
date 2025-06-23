import customtkinter as ctk
import tkinter as tk
from typing import List, Callable, Dict
from google.generativeai.generative_models import GenerativeModel
import assistant_functions
from property_analyzer import PropertyAnalyzer

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
        self.property_analyzer = PropertyAnalyzer()  # Initialize analyzer

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
        self.animation_duration = 50  # milliseconds - target duration
        self.animation_steps = 5  # minimal steps for maximum smoothness
        self.animation_running = False
        
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
        self.analysis_tab = self.tabview.add("📊 Analysis")
        
        # Configure tab layouts
        self.chat_tab.grid_rowconfigure(0, weight=1)
        self.chat_tab.grid_columnconfigure(0, weight=1)
        self.analysis_tab.grid_rowconfigure(0, weight=1)
        self.analysis_tab.grid_columnconfigure(0, weight=1)
        
        # Create chat display in chat tab
        self.chat_display = ctk.CTkTextbox(self.chat_tab, wrap="word")
        self.chat_display.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.chat_display.configure(state="disabled")

        # Set current chat display reference
        self.current_chat = self.chat_display

        # Setup analysis interface
        self._setup_analysis_interface()
        
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
        """Toggle sidebar expansion state with smooth animation"""
        if self.animation_running:
            return
        
        self.animation_running = True
        target_width = self.sidebar_min_width if self.sidebar_expanded else self.sidebar_width
        current_width = self.sidebar_width if self.sidebar_expanded else self.sidebar_min_width
        width_step = (target_width - current_width) / self.animation_steps
        
        def animate_step(step=0):
            if step >= self.animation_steps:
                self.animation_running = False
                self.sidebar_expanded = not self.sidebar_expanded
                # Update button and widget visibility at animation end
                if not self.sidebar_expanded:
                    self.collapse_btn.configure(text="▶")
                    # Hide all widgets except collapse button
                    for widget in self.sidebar.winfo_children():
                        if widget != self.collapse_btn:
                            widget.grid_remove()
                else:
                    self.collapse_btn.configure(text="◀")
                    # Show widgets with proper layout
                    self.settings_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
                    self.appearance_button.grid(row=1, column=0, padx=10, pady=(0, 15), sticky="ew")
                    self.history_label.grid(row=2, column=0, padx=10, pady=(15, 5), sticky="w")
                    self.history_list.grid(row=3, column=0, padx=10, pady=(0, 15), sticky="ew")
                    self.tools_label.grid(row=4, column=0, padx=10, pady=(15, 5), sticky="w")
                    self.tools_desc.grid(row=5, column=0, padx=10, pady=(0, 5), sticky="w")
                    self.tools_scroll.grid(row=6, column=0, padx=10, pady=(0, 10), sticky="ew")
                return
            
            # Calculate current width using easing function
            progress = step / self.animation_steps
            # Optimized cubic easing for smoother motion
            eased_progress = progress * (2 - progress)
            current = current_width + (width_step * self.animation_steps * eased_progress)
            
            # Update sidebar width
            self.sidebar.configure(width=int(current))
            
            # Reposition collapse button
            if self.sidebar_expanded:
                self.collapse_btn.grid(row=0, column=0, padx=(max(current-40, 5), 5), pady=5, sticky="e")
            else:
                # Ensure button remains visible when collapsed
                self.collapse_btn.grid(row=0, column=0, padx=(5, 5), pady=5, sticky="e")
                self.collapse_btn.lift()  # Keep button on top
            
            # Schedule next animation frame
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
    
    def _setup_analysis_interface(self):
        """Set up the property analysis interface"""
        # Create main container with tabs for different analysis types
        self.analysis_tabs = ctk.CTkTabview(self.analysis_tab)
        self.analysis_tabs.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Add analysis type tabs
        self.full_analysis_tab = self.analysis_tabs.add("Full Analysis")
        self.rental_analysis_tab = self.analysis_tabs.add("Rental Analysis")
        self.market_overview_tab = self.analysis_tabs.add("Market Overview")
        
        # Setup each analysis tab
        self._setup_full_analysis_tab()
        self._setup_rental_analysis_tab()
        self._setup_market_overview_tab()
    
    def _setup_full_analysis_tab(self):
        """Set up the full property analysis tab"""
        # Create form frame
        form_frame = ctk.CTkFrame(self.full_analysis_tab)
        form_frame.pack(fill="x", padx=20, pady=20)
        
        # Address input
        ctk.CTkLabel(form_frame, text="Property Address", font=("default", 12, "bold")).pack(pady=(10, 0))
        self.full_address_entry = ctk.CTkEntry(form_frame, placeholder_text="Enter full property address")
        self.full_address_entry.pack(fill="x", padx=20, pady=5)
        
        # Analysis button
        analyze_btn = ctk.CTkButton(
            form_frame,
            text="Analyze Property",
            command=self._run_full_analysis,
            height=40,
            font=("default", 13, "bold")
        )
        analyze_btn.pack(pady=15)
        
        # Results display
        self.full_results_text = ctk.CTkTextbox(self.full_analysis_tab, wrap="word")
        self.full_results_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    
    def _setup_rental_analysis_tab(self):
        """Set up the rental analysis tab"""
        # Create form frame
        form_frame = ctk.CTkFrame(self.rental_analysis_tab)
        form_frame.pack(fill="x", padx=20, pady=20)
        
        # Address input
        ctk.CTkLabel(form_frame, text="Property Address", font=("default", 12, "bold")).pack(pady=(10, 0))
        self.rental_address_entry = ctk.CTkEntry(form_frame, placeholder_text="Enter property address")
        self.rental_address_entry.pack(fill="x", padx=20, pady=5)
        
        # Bedrooms input
        ctk.CTkLabel(form_frame, text="Bedrooms (optional)", font=("default", 12, "bold")).pack(pady=(10, 0))
        self.bedrooms_entry = ctk.CTkEntry(form_frame, placeholder_text="Number of bedrooms")
        self.bedrooms_entry.pack(fill="x", padx=20, pady=5)
        
        # Bathrooms input
        ctk.CTkLabel(form_frame, text="Bathrooms (optional)", font=("default", 12, "bold")).pack(pady=(10, 0))
        self.bathrooms_entry = ctk.CTkEntry(form_frame, placeholder_text="Number of bathrooms")
        self.bathrooms_entry.pack(fill="x", padx=20, pady=5)
        
        # Analysis button
        analyze_btn = ctk.CTkButton(
            form_frame,
            text="Get Rental Analysis",
            command=self._run_rental_analysis,
            height=40,
            font=("default", 13, "bold")
        )
        analyze_btn.pack(pady=15)
        
        # Results display
        self.rental_results_text = ctk.CTkTextbox(self.rental_analysis_tab, wrap="word")
        self.rental_results_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    
    def _setup_market_overview_tab(self):
        """Set up the market overview tab"""
        # Create form frame
        form_frame = ctk.CTkFrame(self.market_overview_tab)
        form_frame.pack(fill="x", padx=20, pady=20)
        
        # Zip code input
        ctk.CTkLabel(form_frame, text="Zip Code", font=("default", 12, "bold")).pack(pady=(10, 0))
        self.zip_code_entry = ctk.CTkEntry(form_frame, placeholder_text="Enter 5-digit zip code")
        self.zip_code_entry.pack(fill="x", padx=20, pady=5)
        
        # Analysis button
        analyze_btn = ctk.CTkButton(
            form_frame,
            text="Get Market Overview",
            command=self._run_market_overview,
            height=40,
            font=("default", 13, "bold")
        )
        analyze_btn.pack(pady=15)
        
        # Results display
        self.market_results_text = ctk.CTkTextbox(self.market_overview_tab, wrap="word")
        self.market_results_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    
    def _display_analysis_results(self, textbox: ctk.CTkTextbox, results: Dict):
        """Helper method to display analysis results in a formatted way"""
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        
        # Format and display results
        formatted_text = "📊 Analysis Results\n\n"
        
        if "property_details" in results:
            formatted_text += "🏠 Property Details:\n"
            details = results["property_details"]
            formatted_text += f"Address: {details.get('address', 'N/A')}\n"
            formatted_text += f"Beds: {details.get('bedrooms', 'N/A')} | "
            formatted_text += f"Baths: {details.get('bathrooms', 'N/A')}\n"
            formatted_text += f"Square Feet: {details.get('squareFeet', 'N/A')}\n\n"
            
        if "rental_estimates" in results:
            formatted_text += "💰 Rental Estimates:\n"
            rental = results["rental_estimates"]
            formatted_text += f"Estimated Rent: ${rental.get('estimatedRent', 'N/A')}/month\n"
            formatted_text += f"Rent Range: ${rental.get('rentRangeLow', 'N/A')} - "
            formatted_text += f"${rental.get('rentRangeHigh', 'N/A')}\n\n"
            
        if "market_statistics" in results:
            formatted_text += "📈 Market Statistics:\n"
            stats = results["market_statistics"]
            formatted_text += f"Median Rent: ${stats.get('medianRent', 'N/A')}\n"
            formatted_text += f"Vacancy Rate: {stats.get('vacancyRate', 'N/A')}%\n"
            formatted_text += f"Rent Growth (YoY): {stats.get('rentGrowthYoY', 'N/A')}%\n\n"
            
        if "ai_insights" in results:
            formatted_text += "🤖 AI Insights:\n"
            formatted_text += results["ai_insights"]
            
        textbox.insert("1.0", formatted_text)
        textbox.configure(state="disabled")
    
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
    
    def _run_full_analysis(self):
        """Run full property analysis"""
        address = self.full_address_entry.get().strip()
        if not address:
            self._show_error("Please enter a property address")
            return
            
        try:
            results = self.property_analyzer.analyze_property(address)
            self._display_analysis_results(self.full_results_text, results)
        except Exception as e:
            self._show_error(f"Analysis failed: {str(e)}")
    
    def _run_rental_analysis(self):
        """Run rental analysis"""
        address = self.rental_address_entry.get().strip()
        if not address:
            self._show_error("Please enter a property address")
            return
            
        try:
            bedrooms = int(self.bedrooms_entry.get()) if self.bedrooms_entry.get() else None
            bathrooms = float(self.bathrooms_entry.get()) if self.bathrooms_entry.get() else None
            
            results = self.property_analyzer.get_detailed_rental_analysis(
                address=address,
                bedrooms=bedrooms,
                bathrooms=bathrooms
            )
            self._display_analysis_results(self.rental_results_text, results)
        except Exception as e:
            self._show_error(f"Rental analysis failed: {str(e)}")
    
    def _run_market_overview(self):
        """Run market overview analysis"""
        zip_code = self.zip_code_entry.get().strip()
        if not zip_code or len(zip_code) != 5 or not zip_code.isdigit():
            self._show_error("Please enter a valid 5-digit zip code")
            return
            
        try:
            results = self.property_analyzer.get_market_overview(zip_code)
            self._display_analysis_results(self.market_results_text, results)
        except Exception as e:
            self._show_error(f"Market overview failed: {str(e)}")