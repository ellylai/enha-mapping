import google.generativeai as genai # make sure this is pip installed
import os

def prompt_llm(prompt: str):
    # --- 1. Load your API key ---
    # Best practice: store your key in an environment variable
    # api_key = os.environ.get("GEMINI_API_KEY")

    # if not api_key:
    #     raise ValueError("API key not found. Please set the GEMINI_API_KEY environment variable.")

    # genai.configure(api_key=api_key)

    # # --- 2. Initialize the model ---
    # # Using the 'flash' model which is fast and capable
    # model = genai.GenerativeModel('gemini-1.5-flash')

    # # --- 3. Send a request ---
    # # prompt = "What are the most common ICD-10 codes for Type 2 Diabetes?"
    # response = model.generate_content(prompt)
    response = "ICD9: 304.20, 304.21, 305.60, 305.61 \nICD10: F14.10, F14.11, F14.12, F14.13, F14.14, F14.15, F14.18, F14.19, F14.20, F14.21, F14.22, F14.23, F14.24, F14.25, F14.28, F14.29, F14.90, F14.91, F14.92, F14.93, F14.94, F14.95, F14.98, F14.99"
    # --- 4. Print the response ---
    return response