import os
import requests
import re

class LLMProcessor:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "ollama")
        self.context_history = []  # Store recent transcriptions for context
        self.max_context = 5  # Keep last 5 transcriptions
        self.interview_context = None
        self.user_profile = None
    
    def set_interview_context(self, interview_context, user_profile):
        """Set interview context and user profile for personalized answers"""
        self.interview_context = interview_context
        self.user_profile = user_profile
    
    def is_question(self, text: str) -> bool:
        """Detect if the text is likely a complete question"""
        text_lower = text.strip().lower()
        
        # Ignore very short texts (incomplete)
        if len(text.split()) < 5:
            return False
        
        # Ignore if ends with incomplete markers
        incomplete_endings = ['what is...', 'is...', 'about...', '...', 'so...', 'like...', 'the...']
        for ending in incomplete_endings:
            if text_lower.endswith(ending):
                return False
        
        # Check for question marks
        if '?' in text:
            return True
        
        complete_question_patterns = [
            'tell me about yourself',
            'describe yourself',
            'what are your strengths',
            'what are your weaknesses',
            'why should we hire you',
            'why do you want',
            'where do you see yourself',
            'describe a time',
            'give me an example',
            'how would you',
            'what would you do',
            'can you tell me about',
            'could you explain',
            'walk me through your',
            'run me through your'
        ]
        
        for pattern in complete_question_patterns:
            if pattern in text_lower:
                return True
        

        if len(text.split()) >= 7:  # At least 7 words for complete question
            question_starters = [
                'what', 'why', 'how', 'when', 'where', 'who',
                'can you', 'could you', 'would you', 'do you',
                'tell me', 'explain', 'describe', 'define'
            ]
            
            for starter in question_starters:
                if text_lower.startswith(starter):
                    return True
        
        return False
    
    def add_to_context(self, text: str):
        """Add transcription to context history"""
        self.context_history.append(text)
        if len(self.context_history) > self.max_context:
            self.context_history.pop(0)
    
    def get_context_string(self) -> str:
        """Get recent context as a string"""
        if not self.context_history:
            return ""
        return " ".join(self.context_history[-3:])  # Last 3 items
    
    def check_accumulated_question(self) -> str:
        """Check if recent context contains a complete question"""
        if len(self.context_history) < 2:
            return None
        
        # Get last few items and combine
        recent = " ".join(self.context_history[-3:])
        
        # Check if this accumulated text is a question
        if self.is_question(recent):
            return recent
        
        return None
        
    def clean_response(self, response: str) -> str:
        """Clean up LLM response by removing formatting artifacts"""
        # Remove common prefixes
        response = re.sub(r'^\*\*Answer:\*\*\s*', '', response, flags=re.IGNORECASE)
        response = re.sub(r'^Answer:\s*', '', response, flags=re.IGNORECASE)
        response = re.sub(r'^\*\*Response:\*\*\s*', '', response, flags=re.IGNORECASE)
        
        # Remove meta-commentary in parentheses at the end
        response = re.sub(r'\n?\*\([^)]+\)\*?\s*$', '', response)
        response = re.sub(r'\n?\([^)]+\)\s*$', '', response)
        
        # Remove "Key points:" sections
        response = re.sub(r'\n?\*?\(Key points:.*?\)\*?\s*$', '', response, flags=re.DOTALL)
        
        return response.strip()
    
    def process(self, text: str, check_question: bool = True) -> str:
        """Process interviewer's speech and return helpful response"""
        response = None
        if self.provider == "ollama":
            response = self._process_ollama(text)
        elif self.provider == "openrouter":
            response = self._process_openrouter(text)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
        
        # Clean up the response
        return self.clean_response(response)
    
    def _process_ollama(self, text: str) -> str:
        """Process using local Ollama"""
        prompt = self._build_prompt(text)
        base_url = os.getenv("OLLAMA_BASE_URL")
        model = os.getenv("OLLAMA_MODEL")
        
        try:
            response = requests.post(
                f"{base_url}/api/generate",  # Correct Ollama endpoint
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            return f"Error with Ollama: {str(e)}\nMake sure Ollama is running: ollama serve"
    
    def _process_openrouter(self, text: str) -> str:
        """Process using OpenRouter API"""
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            return "Error: OPENROUTER_API_KEY not set"
        
        model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
        prompt = self._build_prompt(text)
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a helpful interview assistant. Provide concise, accurate answers to interview questions."},
                        {"role": "user", "content": prompt}
                    ]
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error with OpenRouter: {str(e)}"
    
    def _build_prompt(self, interviewer_text: str) -> str:
        """Build prompt for LLM with context"""
        context = self.get_context_string()
        
        prompt = f"""You are helping answer an interview question.

Question: "{interviewer_text}"
"""
        
        # Add interview context
        if self.interview_context:
            prompt += f"""
Interview Details:
- Company: {self.interview_context.get('company', 'N/A')}
- Position: {self.interview_context.get('position', 'N/A')}
"""
        
        # Add user self intro
        if self.user_profile:
            if 'self_intro' in self.user_profile:
                prompt += f"\nCandidate Background:\n{self.user_profile['self_intro'][:500]}\n"
            
            # Add company background if available
            if 'company_background' in self.user_profile:
                prompt += f"\nCompany Research:\n{self.user_profile['company_background'][:500]}\n"
        
        # Add recent context
        if context and context != interviewer_text:
            prompt += f"\nRecent Context: {context}\n"
        
        prompt += """
Provide a concise answer:
- 2-3 main points
- Use candidate's background if relevant
- Natural tone
- No labels or meta-commentary"""
        
        return prompt

