# CORE LOGIC IS HERE. KEEP WORKING...

import pandas as pd
import typing
from llm_client import OllamaClient

Hypothesis = typing.TypedDict(
    "Hypothesis", {"name": str, "icd9_codes": set[str], "icd10_codes": set[str]}
)


def generate_hypotheses(
    codes: list[str], artificial_break: bool, artificial_slope: float
) -> list[Hypothesis]:
    """
    MOCK FUNCTION, NOT IMPLEMENTED
    Generates mapping hypotheses using GEM files and agentic search placeholders.
    """

    # BASE CASE: NO CODES GENERATED YET
    if not codes:
        # GENERATE NAIVE CODES
        base_prompt = "Give me ONLY comma-separated ICD10 codes for cocaine abuse. Do not provide any other text response."
        response = OllamaClient.invoke(prompt=base_prompt)
        naive_icd10_codes = [str(code).strip() for code in response.split(",")]
        print(f"Naive ICD10 codes generated: {naive_icd10_codes}")
        # TO COMPLETE: map to ICD9 using the files
        # naive_icd9_codes = map(naive_icd10_codes)
        full_list = naive_icd10_codes  # + naive_icd9_codes
        return full_list

    # CASE 1: BAD CODE MAPPING
    elif artificial_break:
        # CASE 1.1: POSITIVE ARTIFICIAL SLOPE (TOO MANY POST-TRANSITION CODES)
        if artificial_slope > 0:
            slope_direction = "positive"
            comment = "There are either extra ICD10 codes or too few ICD9 codes."
        # CASE 1.2: NEGATIVE ARTIFICIAL SLOPE (TOO MANY PRE-TRANSITION CODES)
        else:
            slope_direction = "negative"
            comment = "There are either extra ICD9 codes or too few ICD10 codes."
        new_prompt = f"The following mapping for cocaine abuse does not work. There is a artificially {slope_direction} slope because of the ICD9 to ICD10 code switch. {comment} Please generate a new set of comma-separated codes for me. Do not give me any other response. {codes}"
        response = OllamaClient.invoke(prompt=new_prompt)
        new_codes = [str(code).strip() for code in response.split(",")]
        return new_codes

    # CASE 2: GOOD CODE MAPPING
    else:
        assert not artificial_break
        print(f"Found a good mapping! {codes}")
        return codes
