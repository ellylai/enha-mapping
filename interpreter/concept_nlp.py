import requests
import json
import typing

def mock_llm_invoke(prompt: str) -> str:
    """
    MOCK FUNCTION, NOT IMPLEMENTED
    A dummy function that mimics a real LLM call for debugging.
    """
    print(f"--- MOCK LLM CALLED ---\nPrompt: {prompt[:100]}...")
    # If the prompt is for extraction, return mock key terms
    if "extract the primary clinical concepts" in prompt.lower():
        print("Returning mock key terms...")
        return "cardiomyopathy, atherosclerosis"
    # If the prompt is for expansion, return mock extra terms
    elif "expand it with synonyms" in prompt.lower():
        print("Returning mock expansion terms...")
        return "hypertrophic cardiomyopathy, dilated cardiomyopathy, hardening of arteries, plaque buildup"
    return ""

def get_concept(user_input_desc: str) -> list[str]:
    """
    Identifies and expands on clinical concepts from a user's description using a mock LLM.
    """
    # In a real implementation, you would load your model here.
    # For now, we point to our mock function.
    # MOCK FUNCTION
    llm_invoke = mock_llm_invoke

    # --- Step 1: Get key clinical terms from the initial description ---
    extraction_prompt = f"""
    You are a clinical terminology expert. Analyze the following description and extract the primary clinical concepts.
    Description: "{user_input_desc}"
    ---
    Return only the core concepts as a comma-separated list.
    """
    key_terms_str = llm_invoke(extraction_prompt)
    key_terms = [term.strip() for term in key_terms_str.split(',') if term.strip()]

    if not key_terms:
        print("No key terms found...")
        return []

    # --- Step 2: Expand on the extracted key terms ---
    expansion_prompt = f"""
    You are a clinical terminology expert. Given a list of core medical terms, expand it with synonyms, common sub-types, and closely related concepts.
    Core Terms: "{', '.join(key_terms)}"
    ---
    Return a comma-separated list of these additional terms. Do not repeat the original core terms.
    """
    extras_str = llm_invoke(expansion_prompt)
    extras = [term.strip() for term in extras_str.split(',') if term.strip()]
    
    # --- Step 3: Combine the lists for the final result ---
    category = key_terms + extras

    # Remove duplicates while preserving order
    seen = set()
    seen_return = [x for x in category if not (x in seen or seen.add(x))]
    
    return seen_return
