# PHASE 2
import pandas as pd
import typing

KEYWORDS = []  # keywords generated from the prompt engineering


def generate_relevant_codes() -> list[str]:
    icd9 = pd.read_csv(
        "/zfsauton2/home/ellysel/auton-lab/icd-codes/icd-generator/files/icd9_diagnosis_codes.csv"
    )
    icd10 = pd.read_csv(
        "/zfsauton2/home/ellysel/auton-lab/icd-codes/icd-generator/files/icd10_diagnosis_codes.csv"
    )

    desc_col = "desc"
    code_col = "code"

    if not KEYWORDS:
        return []

    keyword_pattern = "|".join(KEYWORDS)

    naive_list = (
        icd9[icd9[desc_col].str.contains(keyword_pattern, case=False, na=False)][
            code_col
        ].tolist()
        + icd10[icd10[desc_col].str.contains(keyword_pattern, case=False, na=False)][
            code_col
        ].tolist()
    )

    return naive_list
