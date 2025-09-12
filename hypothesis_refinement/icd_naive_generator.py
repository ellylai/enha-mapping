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
    icd9_matches = icd9[icd9[desc_col].str.contains(keyword_pattern, case=False, na=False)]
    icd10_matches = icd10[icd10[desc_col].str.contains(keyword_pattern, case=False, na=False)]
    
    # Add relevance scoring based on keyword match quality
    def calculate_relevance_score(description, search_terms):
        score = 0
        desc_lower = description.lower()
        for term in search_terms:
            if term in desc_lower:
                # Higher score for exact matches, lower for partial
                if f" {term} " in f" {desc_lower} ":
                    score += 2  # Exact word match
                else:
                    score += 1  # Partial match
        return score
    
    # Calculate scores and sort by relevance
    if not icd9_matches.empty:
        icd9_matches = icd9_matches.copy()
        icd9_matches['relevance'] = icd9_matches[desc_col].apply(
            lambda desc: calculate_relevance_score(desc, search_terms)
        )
        icd9_matches = icd9_matches.sort_values('relevance', ascending=False)
        # Limit to top 20 most relevant codes
        icd9_codes = icd9_matches[code_col].tolist()
    else:
        icd9_codes = []
    
    if not icd10_matches.empty:
        icd10_matches = icd10_matches.copy()
        icd10_matches['relevance'] = icd10_matches[desc_col].apply(
            lambda desc: calculate_relevance_score(desc, search_terms)
        )
        icd10_matches = icd10_matches.sort_values('relevance', ascending=False)
        # Limit to top 20 most relevant codes
        icd10_codes = icd10_matches[code_col].tolist()
    else:
        icd10_codes = []
    
    print(f"Found {len(icd9_codes)} ICD-9 codes and {len(icd10_codes)} ICD-10 codes")
    if icd9_codes:
        print(f"Sample ICD-9 codes: {icd9_codes[:5]}")
    if icd10_codes:
        print(f"Sample ICD-10 codes: {icd10_codes[:5]}")
    
    naive_mapping = {"icd9": icd9_codes, "icd10": icd10_codes}
    
    return naive_mapping