import requests
import json
import typing
import sys
import os

# Add parent directory to path to import llm_client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_client import llm_client


def get_concept(user_input_desc: str) -> dict:
    # Directly converts user input to relevant ICD codes using LLM.
    # Returns both medical concepts and ICD codes in one step.
  
    system_message = "You are an expert ICD medical coding specialist. Think thoroughly about all relevant conditions, subtypes, complications, and related codes. After your analysis, provide only the structured format requested."

    # Combined prompt that extracts concepts AND suggests ICD codes
    combined_prompt = f"""Medical description: "{user_input_desc}"

        Please think carefully about this medical description and provide comprehensive ICD coding. Consider all relevant conditions, subtypes, complications, comorbidities, severity levels, and related medical conditions.

        After your analysis, respond with ONLY this exact format:
        CONDITIONS: condition1, condition2, condition3, ...
        ICD9: code1, code2, code3, ...
        ICD10: code1, code2, code3, ...

        Example format:
        CONDITIONS: diabetes mellitus, diabetic complications, diabetic nephropathy, diabetic retinopathy, diabetic neuropathy, diabetic ketoacidosis
        ICD9: 250.0, 250.4, 250.6, 250.5, 362.0, 581.81, 250.1
        ICD10: E11.9, E11.22, E11.21, E11.40, E11.311, E11.620, E11.10

        Analyze and respond:"""

    response = llm_client.invoke(combined_prompt, system_message)
    print(f"Raw LLM response: '{response}'")
    
    # Parse the structured response
    conditions = []
    icd9_codes = []
    icd10_codes = []
    
    lines = response.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('CONDITIONS:'):
            conditions_str = line.replace('CONDITIONS:', '').strip()
            conditions = [c.strip() for c in conditions_str.split(',') if c.strip()]
        elif line.startswith('ICD9:'):
            icd9_str = line.replace('ICD9:', '').strip()
            icd9_codes = [c.strip() for c in icd9_str.split(',') if c.strip()]
        elif line.startswith('ICD10:'):
            icd10_str = line.replace('ICD10:', '').strip()
            icd10_codes = [c.strip() for c in icd10_str.split(',') if c.strip()]
    
    # Fallback if parsing fails
    if not conditions and not icd9_codes and not icd10_codes:
        print("Parsing failed, using fallback...")
        return {
            "concepts": ["substance dependence"],
            "icd9": ["304.00"],  # Fallback ICD-9
            "icd10": ["F19.20"]  # Fallback ICD-10
        }
    
    print(f"Extracted conditions: {conditions}")
    print(f"Extracted ICD-9: {icd9_codes}")
    print(f"Extracted ICD-10: {icd10_codes}")
    
    return {
        "concepts": conditions,
        "icd9": icd9_codes,
        "icd10": icd10_codes
    }
