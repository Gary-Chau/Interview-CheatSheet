import os
import time
from dotenv import load_dotenv
from src.stt import STT
from src.llm_processor import LLMProcessor
from src.gui import InterviewGUI

load_dotenv()

class InterviewCheatSheet:
    def __init__(self, gui=None):
        self.gui = gui
        self.llm_processor = LLMProcessor()
        self.stt = None
        self.processed_questions = []  # Track processed questions to avoid duplicates
        self.user_profile = None
        self.interview_context = None
        
    def is_similar_question(self, question: str) -> bool:
        """Check if this question is similar to recently processed ones"""
        question_words = set(question.lower().split())
        
        for prev_q in self.processed_questions[-3:]:  # Check last 3 questions
            prev_words = set(prev_q.lower().split())
            # Calculate similarity (Jaccard index)
            if len(question_words) > 0 and len(prev_words) > 0:
                similarity = len(question_words & prev_words) / len(question_words | prev_words)
                if similarity > 0.7:  # 70% similar = duplicate
                    return True
        return False
        
    def start_stt_processing(self):
        """Start STT processing in background"""
        # Get context from GUI
        self.interview_context = self.gui.interview_context
        self.user_profile = self.gui.user_profile
        
        # Set context in LLM processor
        self.llm_processor.set_interview_context(
            self.interview_context,
            self.user_profile
        )
        
        self.gui.update_status("Initializing STT...")
        
        # Get device config from env or use defaults
        device = os.getenv("STT_DEVICE", "cuda")  
        model_size = os.getenv("STT_MODEL", "base.en")  # tiny.en, base.en, small.en, medium.en
        
        try:
            # Initialize STT with faster-whisper
            self.stt = STT(
                model_size=model_size,
                device=device,
                compute_type="int8" if device == "cpu" else "float16",
                language="en",
                logging_level="WARNING"
            )
            
            # Start listening in background
            self.stt.listen()
            
            self.gui.update_status("Listening to system audio...")
            
            # Main loop - check for new transcriptions
            while self.stt.is_listening and self.gui.root.winfo_exists():
                transcription = self.stt.get_last_transcription()
                
                if transcription:
                    # Add to context history
                    self.llm_processor.add_to_context(transcription)
                    
                    question_to_process = None
                    
                    # Check if current transcription is a question
                    if self.llm_processor.is_question(transcription):
                        question_to_process = transcription
                    else:
                        # Check if accumulated context forms a question
                        accumulated = self.llm_processor.check_accumulated_question()
                        if accumulated:
                            question_to_process = accumulated
                    
                    # Process question if found and not a duplicate
                    if question_to_process and not self.is_similar_question(question_to_process):
                        # Check minimum quality - must be at least 5 words
                        if len(question_to_process.split()) >= 5:
                            self.gui.add_question(question_to_process)
                            self.gui.update_status("Generating answer...")
                            
                            # Process with LLM
                            response = self.llm_processor.process(question_to_process)
                            self.gui.add_answer(response)
                            self.gui.update_status("Listening...")
                            
                            # Track this question
                            self.processed_questions.append(question_to_process)
                            if len(self.processed_questions) > 10:  # Keep last 10
                                self.processed_questions.pop(0)
                    else:
                        # Just show transcription without processing
                        self.gui.add_transcription(transcription)
                
                time.sleep(0.5)
                
        except Exception as e:
            if self.gui:
                self.gui.update_status(f"Error: {str(e)}")
            if self.stt:
                self.stt.stop()

def main():
    """Main entry point for the application"""
    # Create GUI with callback
    def on_start(gui):
        app = InterviewCheatSheet(gui)
        app.start_stt_processing()
    
    gui = InterviewGUI(on_start)
    gui.run()

if __name__ == "__main__":
    main()

