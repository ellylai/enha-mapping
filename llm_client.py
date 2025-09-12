import requests
import json
import os

class OllamaClient:
    """Simple client for Ollama LLM integration"""
    
    def __init__(self, model="deepseek-r1:7b", base_url="http://localhost:11434"):
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
                        "temperature": 0.1,  # Lower temperature for more focused responses
                        "num_predict": 1000,  # Much more tokens to allow complete reasoning + comprehensive answer
                        "top_p": 0.9,        # More focused sampling
                        "repeat_penalty": 1.1,  # Reduce repetition
                        "stop": []  # Let it complete naturally
                    }
                },
                timeout=60  # Much longer timeout to allow full reasoning without interruption
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
                
                # Remove DeepSeek R1 reasoning tags
                if '<think>' in response_text:
                    # Extract everything after </think> if it exists
                    if '</think>' in response_text:
                        response_text = response_text.split('</think>')[-1]
                    else:
                        # If thinking is incomplete, try to extract structured lines from the raw response
                        lines = response_text.split('\n')
                        structured_lines = []
                        for line in lines:
                            if any(line.strip().startswith(prefix) for prefix in ['CONDITIONS:', 'ICD9:', 'ICD10:']):
                                structured_lines.append(line.strip())
                        if structured_lines:
                            response_text = '\n'.join(structured_lines)
                        else:
                            # If no structured lines found, return empty to trigger fallback
                            response_text = ""
                
                # Clean up conversational phrases
                response_text = response_text.replace("Based on the description", "")
                response_text = response_text.replace("I extracted the following", "")
                response_text = response_text.replace("The primary clinical concepts are:", "")
                response_text = response_text.replace("Here are", "")
                response_text = response_text.strip().strip(":")
                
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
