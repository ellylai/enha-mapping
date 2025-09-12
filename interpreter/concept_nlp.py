import requests
import json
import typing
import sys
import os

# Add parent directory to path to import llm_client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_client import llm_client

def clean_llm_response(response_text: str) -> list[str]:
    """
    Robustly clean LLM response to extract only medical condition names.
    """
    # Remove common conversational phrases
    cleanup_phrases = [
        "based on the description",
        "i extracted the following",
        "the primary clinical concepts are:",
        "here are",
        "output:",
        "answer:",
        "medical conditions:",
        "the conditions are:",
        "related conditions:",
        "icd conditions:"
    ]
    
    cleaned = response_text.lower()
    for phrase in cleanup_phrases:
        cleaned = cleaned.replace(phrase, "")
    
    # Split by lines and find the line with actual conditions
    lines = cleaned.split('\n')
    condition_line = ""
    
    for line in lines:
        line = line.strip()
        # Skip empty lines and lines that start with conversational words
        if (line and 
            not line.startswith(('the ', 'i ', 'here', 'based', 'this', 'these', 'answer', 'output')) and
            (',' in line or any(word in line for word in ['diabetes', 'cardio', 'hyper', 'syndrome', 'disorder', 'disease']))):
            condition_line = line
            break
    
    if not condition_line:
        condition_line = cleaned.strip()
    
    # Extract conditions from the line
    conditions = []
    for term in condition_line.split(','):
        term = term.strip().strip('.:()-"\'')
        # Filter out non-medical terms and short words
        if (term and 
            len(term) > 2 and 
            not term.startswith(('the ', 'i ', 'here', 'based', 'this', 'answer')) and
            not term.isdigit()):
            conditions.append(term)
    
    return conditions

def get_concept(user_input_desc: str) -> list[str]:
    """
    Identifies and expands on clinical concepts from a user's description using Ollama LLM.
    """
    # --- Step 1: Get key clinical terms from the initial description ---
    system_message = "You are an ICD medical coding specialist. You must respond with ONLY medical condition names separated by commas. No explanations, no conversational text."
    
    extraction_prompt = f"""Extract ICD-appropriate medical conditions from: "{user_input_desc}"

Rules:
- Return ONLY condition names
- Separate with commas
- No explanations or extra text
- Use precise medical terminology

Examples:
Input: "diabetes" → Output: diabetes mellitus
Input: "heart problems" → Output: cardiomyopathy, heart failure
Input: "drug addiction" → Output: substance dependence, opioid use disorder

Output:"""
    
    key_terms_str = llm_client.invoke(extraction_prompt, system_message)
    print(f"Raw LLM response for extraction: '{key_terms_str}'")
    
    # Use the new robust cleaning function
    key_terms = clean_llm_response(key_terms_str)
    
    print(f"Cleaned key terms: {key_terms}")

    if not key_terms:
        print("No key terms found, using fallback")
        return ["substance dependence", "opioid abuse"]  # More ICD-appropriate fallback

    # --- Step 2: Expand on the extracted key terms ---
    expansion_prompt = f"""Add related ICD conditions to: {', '.join(key_terms)}

Rules:
- Return ONLY condition names
- Separate with commas  
- No explanations or extra text
- Include subtypes and related conditions

Examples:
Input: cardiomyopathy → Output: hypertrophic cardiomyopathy, dilated cardiomyopathy, restrictive cardiomyopathy
Input: substance dependence → Output: opioid dependence, alcohol dependence, drug withdrawal syndrome

Output:"""
    
    extras_str = llm_client.invoke(expansion_prompt, system_message)
    print(f"Raw LLM response for expansion: '{extras_str}'")
    
    # Use the robust cleaning function for expansion too
    extras = clean_llm_response(extras_str)
    
    # Remove duplicates between key_terms and extras
    extras = [term for term in extras if term not in key_terms]
    
    print(f"Cleaned expansion terms: {extras}")
    
    # --- Step 3: Combine the lists for the final result ---
    category = key_terms + extras

    # Remove duplicates while preserving order
    seen = set()
    seen_return = [x for x in category if not (x in seen or seen.add(x))]
    return seen_return
