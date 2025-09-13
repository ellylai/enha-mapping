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
        # Invoke the LLM with a prompt and optional system message
        
        return self._mock_fallback(prompt)

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
                        "temperature": 0.1,  # Lower temperature for more focused responses
                        "num_predict": 1000,  # Much more tokens to allow complete reasoning + comprehensive answer
                        "top_p": 0.9,        # More focused sampling
                        "repeat_penalty": 1.1,  # Reduce repetition
                        "stop": []  # Let it complete naturally
                    }
                },
                timeout=30  
            )
            
            if response.status_code == 200:
                result = response.json()
                raw_response = result.get("response", "").strip()
                
                print("📥 RAW OLLAMA RESPONSE:")
                print("-" * 40)
                print(f"'{raw_response}'")
                print("-" * 40)
                
                # Clean up the response - remove reasoning tags and conversational phrases
                response_text = raw_response
                
                print("🧹 CLEANED RESPONSE:")
                print("-" * 40)
                print(f"'{response_text}'")
                print("-" * 40)
                print("="*80)
                print()
                
                return response_text
            else:
                print(f"❌ Ollama API error: {response.status_code}")
                return self._mock_fallback(prompt)
                
        except Exception as e:
            print(f"❌ Ollama connection error: {e}")
            print("🔄 Falling back to mock responses...")
            return self._mock_fallback(prompt)
    
    def _mock_fallback(self, prompt):
        """Fallback to mock responses if Ollama is unavailable"""
        print("--- USING MOCK LLM (Ollama unavailable) ---")
        
        return "Mock response - Ollama unavailable"

# Global instance
llm_client = OllamaClient()
