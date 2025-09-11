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

    # Create a regex pattern to find any of the keywords
    keyword_pattern = '|'.join(keywords)
    
    # Filter each dataframe for descriptions containing the keywords
    icd9_codes = icd9[icd9[desc_col].str.contains(keyword_pattern, case=False, na=False)][code_col].tolist()
    icd10_codes = icd10[icd10[desc_col].str.contains(keyword_pattern, case=False, na=False)][code_col].tolist()
    
    naive_mapping = {"icd9": icd9_codes, "icd10": icd10_codes}
    
    return naive_mapping