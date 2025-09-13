import pandas as pd


def icd_map(icd10_codes: list[str]):
    icd10_to_icd9_gem = pd.read_csv("hypothesis_refinement/files/icd10cmtoicd9gem.csv")
    
    mapped_rows = icd10_to_icd9_gem[icd10_to_icd9_gem['icd10cm'].isin(icd10_codes)]
    # Get the unique corresponding ICD-9 codes
    icd9_codes = mapped_rows['icd9cm'].unique().tolist()
    
    return icd9_codes