# CORE LOGIC IS HERE. KEEP WORKING...

import pandas as pd
import typing
from interpreter.llm_client import llm_client
from .  icd_mapping_script import icd_map

Hypothesis = typing.TypedDict(
    "Hypothesis", {"name": str, "icd9_codes": set[str], "icd10_codes": set[str]}
)

ARTIFICAL_BREAK_FLAG = False

def generate_hypotheses(
    codes: list[str], artificial_break: bool, artificial_slope: float, user_input_desc=""
) -> list[Hypothesis]:
    """
    MOCK FUNCTION, NOT IMPLEMENTED
    Generates mapping hypotheses using GEM files and agentic search placeholders.
    """
    system_message = "You are an expert ICD medical coding specialist. After your analysis, provide only the answer, without any commentary or text response."

    combined_prompt = f"""Medical description: "{user_input_desc}"

        Please think carefully about this medical description and provide comprehensive ICD coding. Consider all relevant conditions, subtypes, complications, comorbidities, severity levels, and related medical conditions.

        After your analysis, respond with ONLY this exact format:
        ICD9: code1, code2, code3, ...
        ICD10: code1, code2, code3, ...

        Example format:
        ICD9: 250.0, 250.4, 250.6, 250.5, 362.0, 581.81, 250.1
        ICD10: E11.9, E11.22, E11.21, E11.40, E11.311, E11.620, E11.10

        Analyze and respond:"""

    # BASE CASE: NO CODES GENERATED YET
    if not codes:
        # GENERATE NAIVE CODES
        base_prompt = "Give me ONLY comma-separated ICD10 codes. Do not provide any other text response."
        response = llm_client.invoke(base_prompt)

        # strip off ICD labels and split
        cleaned = response.replace("ICD10:", "").replace("ICD9:", "").strip()
        naive_icd10_codes = [c.strip() for c in cleaned.split(",") if c.strip()]
        print(f"Naive ICD10 codes generated: {naive_icd10_codes}")

        naive_icd9_codes = icd_map(naive_icd10_codes)

        return [{
            "name": "naive mapping",
            "icd9_codes": set(naive_icd9_codes),
            "icd10_codes": set(naive_icd10_codes),
        }]

    # CASE 1: BAD CODE MAPPING
    elif artificial_break and ARTIFICAL_BREAK_FLAG:
        # CASE 1.1: POSITIVE ARTIFICIAL SLOPE (TOO MANY POST-TRANSITION CODES)
        if artificial_slope > 0:
            slope_direction = "positive"
            comment = "There are either extra ICD10 codes or too few ICD9 codes."
        # CASE 1.2: NEGATIVE ARTIFICIAL SLOPE (TOO MANY PRE-TRANSITION CODES)
        else:
            slope_direction = "negative"
            comment = "There are either extra ICD9 codes or too few ICD10 codes."
        new_prompt = f"The following mapping for cocaine abuse does not work. There is a artificially {slope_direction} slope because of the ICD9 to ICD10 code switch. {comment} Please generate a new set of comma-separated codes for me. Do not give me any other response. {codes}"
        response = llm_client.invoke(new_prompt)
        new_codes = [c.strip() for c in response.split(",") if c.strip()]
        return [{
            "name": "adjusted mapping",
            "icd9_codes": set(icd_map(new_codes)),
            "icd10_codes": set(new_codes),
        }]

    # CASE 2: GOOD CODE MAPPING
    else:
        # assert not artificial_break ---- TURN ON FOR ELIF CASE ----
        print(f"Found a good mapping! {codes}")
        return [{
            "name": "baseline mapping",
            "icd9_codes": set(codes.get("icd9", [])) if isinstance(codes, dict) else set(),
            "icd10_codes": set(codes.get("icd10", [])) if isinstance(codes, dict) else set(),
        }]
