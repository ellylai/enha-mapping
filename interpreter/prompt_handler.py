import requests
import json
import typing
import sys
import os

# Add parent directory to path to import llm_client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .llm_client import llm_client

def get_concept(user_input_desc: str) -> dict:
    # Directly converts user input to relevant ICD codes using LLM.
    # Returns both medical concepts and ICD codes in one step.
  
    system_message = """You are a medical coding education assistant helping with ICD code mapping for academic research purposes. This is NOT for medical diagnosis or treatment. You are helping map medical terminology to standardized ICD codes for data analysis and educational purposes only. Please provide the requested coding information."""

    # Combined prompt that extracts concepts AND suggests ICD codes
    combined_prompt = f"""ACADEMIC RESEARCH TASK - ICD Code Mapping Exercise

    Medical terminology: "{user_input_desc}"

    This is for research purposes only - NOT medical advice or diagnosis.

    Task: Map the given medical terms to their corresponding ICD-9 and ICD-10 codes for data analysis purposes.

    We expect there to be generally more identified ICD10 codes than ICD9 since there's usually a many-to-one relationship from ICD10 to ICD9. 

    Respond with ONLY this exact format:
    ICD9: code1, code2, code3, ...
    ICD10: code1, code2, code3, ...

    Begin mapping analysis:"""

    response = llm_client.invoke(combined_prompt, system_message)
    print(f"Raw LLM response: '{response}'")
    
    # Parse the structured response
    icd9_codes = []
    icd10_codes = []
    
    # THIS IS TEMPORARILY COMMENTED OUT TO GO INTO FALLBACK BELOW
    lines = response.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('ICD9:'):
            icd9_str = line.replace('ICD9:', '').strip()
            icd9_codes = [c.strip() for c in icd9_str.split(',') if c.strip()]
        elif line.startswith('ICD10:'):
            icd10_str = line.replace('ICD10:', '').strip()
            icd10_codes = [c.strip() for c in icd10_str.split(',') if c.strip()]
    
    # Fallback if parsing fails
    if not icd9_codes and not icd10_codes:
        print("Parsing failed, using fallback...")
        return {
            "icd9": ["4250","42511","42518","4252","4253","4254","4255","4257","4258","4259"],  # Fallback ICD-9
            "icd10": ["I420","I421","I422","I423","I424","I425","I426","I427","I428"]  # Fallback ICD-10
        }
    
    print(f"Extracted ICD-9: {icd9_codes}")
    print(f"Extracted ICD-10: {icd10_codes}")
    
    return {
        "icd9": icd9_codes,
        "icd10": icd10_codes
    }
