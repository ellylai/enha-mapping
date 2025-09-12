# PHASE 2
import pandas as pd
import typing

def generate_relevant_codes(keywords: list[str]) -> dict:
    """
    Generates a naive list of ICD-9 and ICD-10 codes based on keywords.
    """
    icd9 = pd.read_csv("icd_generator/files/icd9_diagnosis_codes.csv")
    icd10 = pd.read_csv("icd_generator/files/icd10_diagnosis_codes.csv")
    
    desc_col = "desc"
    code_col = "code"
    
    if not keywords:
        return {"icd9": [], "icd10": []}

    print(f"Searching for keywords: {keywords}")
    
    # Process keywords to extract root medical terms
    search_terms = []
    for keyword in keywords:
        keyword = keyword.strip().lower()
        
        # Extract root medical terms
        if 'opioid' in keyword or 'heroin' in keyword:
            search_terms.extend(['opioid', 'opiate', 'dependence'])
        elif 'cardiomyopathy' in keyword:
            search_terms.extend(['cardiomyopathy'])
        elif 'atherosclerosis' in keyword:
            search_terms.extend(['atherosclerosis', 'arteriosclerosis'])
        else:
            # For other terms, try to extract the core medical word
            words = keyword.replace('use disorder', '').replace('disorder', '').strip().split()
            if words:
                search_terms.extend(words)
    
    # Remove duplicates and empty strings
    search_terms = [term for term in set(search_terms) if term and len(term) > 2]
    print(f"Search terms: {search_terms}")
    
    # Create a regex pattern to find any of the search terms
    if not search_terms:
        return {"icd9": [], "icd10": []}
        
    keyword_pattern = '|'.join(search_terms)
    
    # Filter each dataframe for descriptions containing the keywords
    icd9_codes = icd9[icd9[desc_col].str.contains(keyword_pattern, case=False, na=False)][code_col].tolist()
    icd10_codes = icd10[icd10[desc_col].str.contains(keyword_pattern, case=False, na=False)][code_col].tolist()
    
    print(f"Found {len(icd9_codes)} ICD-9 codes and {len(icd10_codes)} ICD-10 codes")
    if icd9_codes:
        print(f"Sample ICD-9 codes: {icd9_codes[:5]}")
    if icd10_codes:
        print(f"Sample ICD-10 codes: {icd10_codes[:5]}")
    
    naive_mapping = {"icd9": icd9_codes, "icd10": icd10_codes}
    
    return naive_mapping