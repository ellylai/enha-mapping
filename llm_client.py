import requests
import json
import os

class OllamaClient:
    """Simple client for Ollama LLM integration"""
    
    def __init__(self, model="llama3.2:3b", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.use_ollama = os.getenv("USE_OLLAMA", "true").lower() == "true"
    
    def invoke(self, prompt: str, system_message: str = None) -> str:
        """Invoke the LLM with a prompt and optional system message"""
        
        if not self.use_ollama:
            return self._mock_fallback(prompt)
        
        # Create a cleaner prompt format
        full_prompt = prompt
        if system_message:
            full_prompt = f"{system_message}\n\n{prompt}"
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.05,  # Very low temperature for consistent medical terminology
                        "num_predict": 80,    # Even shorter for focused responses
                        "top_p": 0.8,
                        "repeat_penalty": 1.1,
                        "stop": ["\n", "Note:", "Example:", "Format:", "ICD", "The", "These"]  # Stop on explanatory text
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "").strip()
                # Clean up the response - remove common conversational phrases
                response_text = response_text.replace("Based on the description", "")
                response_text = response_text.replace("I extracted the following", "")
                response_text = response_text.replace("The primary clinical concepts are:", "")
                response_text = response_text.replace("Here are", "")
                response_text = response_text.strip().strip(":")
                return response_text
            else:
                print(f"Ollama API error: {response.status_code}")
                return self._mock_fallback(prompt)
                
        except Exception as e:
            print(f"Ollama connection error: {e}")
            print("Falling back to mock responses...")
            return self._mock_fallback(prompt)
    
    def _mock_fallback(self, prompt):
        """Fallback to mock responses if Ollama is unavailable"""
        print("--- USING MOCK LLM (Ollama unavailable) ---")
        
        if "extract icd-relevant" in prompt.lower() or "medical terms" in prompt.lower():
            if "heroin" in prompt.lower() or "opioid" in prompt.lower() or "addiction" in prompt.lower():
                return "opioid dependence, substance abuse"
            elif "cardiomyopathy" in prompt.lower():
                return "cardiomyopathy, heart failure"
            elif "atherosclerosis" in prompt.lower():
                return "atherosclerosis, coronary artery disease"
            else:
                return "substance abuse, dependence"
        elif "related icd terms" in prompt.lower():
            if "opioid" in prompt.lower():
                return "opioid intoxication, opioid withdrawal, heroin dependence"
            elif "cardiomyopathy" in prompt.lower():
                return "dilated cardiomyopathy, hypertrophic cardiomyopathy"
            else:
                return "chronic dependence, acute intoxication"
        
        return "Mock response - Ollama unavailable"

# Global instance
llm_client = OllamaClient()
