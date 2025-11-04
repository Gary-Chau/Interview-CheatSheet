"""
Complete GUI for Interview Cheat Sheet with Chat Interface
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
from pathlib import Path
import threading


class InterviewGUI:
    def __init__(self, on_start_callback):
        self.on_start_callback = on_start_callback
        self.root = tk.Tk()
        self.root.title("Interview Cheat Sheet")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        self.interview_context = {}
        self.user_profile = {}
        self.setup_complete = False
        self.running = False
        
        self.create_setup_screen()
        
    def create_setup_screen(self):
        """Create initial setup screen"""
        self.setup_frame = ttk.Frame(self.root, padding="40")
        self.setup_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = tk.Label(self.setup_frame, text="Interview Assistant Setup", 
                        font=("Arial", 20, "bold"), bg='#f0f0f0')
        title.pack(pady=30)
        
        # Form
        form_frame = ttk.Frame(self.setup_frame)
        form_frame.pack()
        
        # Company
        ttk.Label(form_frame, text="Company:", font=("Arial", 11)).grid(row=0, column=0, sticky=tk.W, pady=10, padx=5)
        self.company_entry = ttk.Entry(form_frame, width=30, font=("Arial", 11))
        self.company_entry.grid(row=0, column=1, pady=10, padx=5)
        self.company_entry.focus()
        
        # Position
        ttk.Label(form_frame, text="Position:", font=("Arial", 11)).grid(row=1, column=0, sticky=tk.W, pady=10, padx=5)
        self.position_entry = ttk.Entry(form_frame, width=30, font=("Arial", 11))
        self.position_entry.grid(row=1, column=1, pady=10, padx=5)
        
        # Date
        ttk.Label(form_frame, text="Date:", font=("Arial", 11)).grid(row=2, column=0, sticky=tk.W, pady=10, padx=5)
        self.date_entry = ttk.Entry(form_frame, width=30, font=("Arial", 11))
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=2, column=1, pady=10, padx=5)
        
        # Start button
        start_btn = tk.Button(form_frame, text="Start", font=("Arial", 12, "bold"),
                             bg='#4CAF50', fg='white', padx=20, pady=10,
                             command=self.on_start)
        start_btn.grid(row=3, column=0, columnspan=2, pady=30)
        
        # Status
        self.status_label = tk.Label(self.setup_frame, text="", font=("Arial", 10), bg='#f0f0f0')
        self.status_label.pack(pady=10)
        
    def load_profile(self):
        """Load self intro and company background"""
        profile = {}
        database_path = Path("database")
        
        # Load self intro
        intro_path = database_path / "self_intro.txt"
        if intro_path.exists():
            with open(intro_path, 'r', encoding='utf-8') as f:
                profile['self_intro'] = f.read()
        
        # Load company background
        company = self.company_entry.get().strip().lower().replace(" ", "_")
        if company:
            company_path = database_path / f"company_{company}.txt"
            if company_path.exists():
                with open(company_path, 'r', encoding='utf-8') as f:
                    profile['company_background'] = f.read()
        
        return profile
        
    def on_start(self):
        """Handle start button click"""
        company = self.company_entry.get().strip()
        position = self.position_entry.get().strip()
        date = self.date_entry.get().strip()
        
        if not company:
            self.status_label.config(text="Please enter company name", fg="red")
            return
        
        if not position:
            self.status_label.config(text="Please enter position", fg="red")
            return
        
        self.interview_context = {
            'company': company,
            'position': position,
            'date': date
        }
        
        self.user_profile = self.load_profile()
        self.setup_complete = True
        
        # Switch to chat interface
        self.setup_frame.destroy()
        self.create_chat_interface()
        
        # Start background processing
        threading.Thread(target=self.on_start_callback, args=(self,), daemon=True).start()
        
    def create_chat_interface(self):
        """Create chat interface"""
        # Header
        header = tk.Frame(self.root, bg='#2196F3', height=60)
        header.pack(fill=tk.X)
        
        title = tk.Label(header, 
                        text=f"Interview: {self.interview_context['company']} - {self.interview_context['position']}", 
                        font=("Arial", 14, "bold"), bg='#2196F3', fg='white')
        title.pack(pady=15)
        
        # Chat display
        chat_frame = ttk.Frame(self.root)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.chat_display = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, 
                                                       font=("Arial", 10), bg='white',
                                                       state=tk.DISABLED)
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_bar = tk.Label(self.root, text="Listening...", 
                                   font=("Arial", 9), bg='#f0f0f0', anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        
    def add_transcription(self, text):
        """Add transcription to chat"""
        self.root.after(0, self._add_message, f"[Transcribed]: {text}", "#666666")
        
    def add_question(self, question):
        """Add detected question to chat"""
        self.root.after(0, self._add_message, f"\nQUESTION:\n{question}\n", "#FF5722", True)
        
    def add_answer(self, answer):
        """Add AI answer to chat"""
        self.root.after(0, self._add_message, f"ANSWER:\n{answer}\n{'='*60}\n", "#4CAF50", True)
        
    def _add_message(self, text, color, bold=False):
        """Internal method to add message to chat display"""
        self.chat_display.config(state=tk.NORMAL)
        
        # Create tag for this message
        tag_name = f"tag_{len(self.chat_display.get('1.0', tk.END))}"
        
        self.chat_display.insert(tk.END, text + "\n")
        
        # Apply formatting
        start_index = self.chat_display.index(f"end-{len(text)+2}c")
        end_index = self.chat_display.index("end-2c")
        
        self.chat_display.tag_add(tag_name, start_index, end_index)
        self.chat_display.tag_config(tag_name, foreground=color)
        if bold:
            self.chat_display.tag_config(tag_name, font=("Arial", 10, "bold"))
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        
    def update_status(self, text):
        """Update status bar"""
        self.root.after(0, lambda: self.status_bar.config(text=text))
        
    def run(self):
        """Run the GUI"""
        self.root.mainloop()
