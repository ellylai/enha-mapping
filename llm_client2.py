import google.generativeai as genai # make sure this is pip installed
import os

def prompt_llm(prompt: str):
    # --- 1. Load your API key ---
    # Best practice: store your key in an environment variable
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("API key not found. Please set the GEMINI_API_KEY environment variable.")

    genai.configure(api_key=api_key)

    # --- 2. Initialize the model ---
    # Using the 'flash' model which is fast and capable
    model = genai.GenerativeModel('gemini-1.5-flash')

    # --- 3. Send a request ---
    # prompt = "What are the most common ICD-10 codes for Type 2 Diabetes?"
    response = model.generate_content(prompt)

    # --- 4. Print the response ---
    return response.text