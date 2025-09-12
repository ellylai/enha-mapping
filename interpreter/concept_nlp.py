import requests
import json
import typing
import sys
import os

# Add parent directory to path to import llm_client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_client import llm_client

def get_concept(user_input_desc: str) -> list[str]:
    """
    Identifies and expands on clinical concepts from a user's description using Ollama LLM.
    """
    # --- Step 1: Get key clinical terms from the initial description ---
    system_message = "You are an ICD medical coding specialist. Return only medical condition names, nothing else."
    
    extraction_prompt = f"""Text: "{user_input_desc}"

Extract medical conditions for ICD coding. Return ONLY possible condition names separated by commas.

Examples:
- "diabetes" → diabetes mellitus
- "heart problems" → cardiomyopathy
- "drug addiction" → substance dependence

Answer:"""
    
    key_terms_str = llm_client.invoke(extraction_prompt, system_message)
    print(f"Raw LLM response for extraction: '{key_terms_str}'")
    
    # Clean and parse the response properly
    key_terms_str = key_terms_str.strip()
    # Remove everything before the first medical term
    lines = key_terms_str.split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith(('Answer:', 'Based', 'The', 'I', 'Here', 'Medical')):
            key_terms_str = line
            break
    
    # Split by commas and clean each term
    key_terms = []
    for term in key_terms_str.split(','):
        term = term.strip().strip('.:')  # Remove periods and colons
        if term and len(term) > 2 and not term.startswith(('Based', 'The', 'I', 'Here')):
            key_terms.append(term)
    
    print(f"Cleaned key terms: {key_terms}")

    if not key_terms:
        print("No key terms found, using fallback")
        return ["substance dependence", "opioid abuse"]  # More ICD-appropriate fallback

    # --- Step 2: Expand on the extracted key terms ---
    expansion_prompt = f"""Medical conditions: {', '.join(key_terms)}

Add related ICD conditions. Return ONLY condition names separated by commas.

Examples:
- cardiomyopathy → hypertrophic cardiomyopathy, dilated cardiomyopathy
- substance dependence → opioid dependence, drug withdrawal

Answer:"""
    
    extras_str = llm_client.invoke(expansion_prompt, system_message)
    print(f"Raw LLM response for expansion: '{extras_str}'")
    
    # Clean and parse the expansion response
    extras_str = extras_str.strip()
    # Remove everything before the first medical term
    lines = extras_str.split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith(('Answer:', 'Based', 'The', 'I', 'Here', 'Related')):
            extras_str = line
            break
    
    # Split by commas and clean each term
    extras = []
    for term in extras_str.split(','):
        term = term.strip().strip('.:')  # Remove periods and colons
        if term and len(term) > 2 and term not in key_terms and not term.startswith(('Based', 'The', 'I', 'Here')):
            extras.append(term)
    
    print(f"Cleaned expansion terms: {extras}")
    
    # --- Step 3: Combine the lists for the final result ---
    category = key_terms + extras

    # Remove duplicates while preserving order
    seen = set()
    seen_return = [x for x in category if not (x in seen or seen.add(x))]
    return seen_return
