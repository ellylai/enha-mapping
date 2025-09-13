# CORE LOGIC IS HERE. KEEP WORKING...

import pandas as pd
import typing
from .icd_parsing_script import icd_map, parse_codes
from interpreter.prompt_handler import get_concept

Hypothesis = typing.TypedDict(
    "Hypothesis", {"name": str, "icd9_codes": set[str], "icd10_codes": set[str]}
)


def generate_hypotheses(
    codes: dict,
    artificial_break: bool,
    artificial_slope: float,
    user_input_desc="",
) -> Hypothesis:

    # BASE CASE: NO CODES GENERATED YET -> GENERATE NAIVE CODES
    if not codes:
        raw_codes = get_concept(user_input_desc)
        naive_icd9_codes = parse_codes(raw_codes["icd9"])
        naive_icd10_codes = parse_codes(raw_codes["icd10"])

        print(f"Naive codes generated: {naive_icd9_codes + naive_icd10_codes}")

        return {
            "name": "naive mapping",
            "icd9_codes": set(naive_icd9_codes),
            "icd10_codes": set(naive_icd10_codes),
        }

    # CASE 1: BAD CODE MAPPING -> GENERATE HYPOTHESIS
    elif artificial_break:
        # CASE 1.1: POSITIVE ARTIFICIAL SLOPE (TOO MANY POST-TRANSITION CODES)
        if artificial_slope > 0:
            slope_direction = "positive"
            comment = "There are either extra ICD10 codes or too few ICD9 codes."
        # CASE 1.2: NEGATIVE ARTIFICIAL SLOPE (TOO MANY PRE-TRANSITION CODES)
        else:
            slope_direction = "negative"
            comment = "There are either extra ICD9 codes or too few ICD10 codes."
        supplementary_prompt = f"""
        You have already generated some mappings for me, but the following mappings for "{user_input_desc}" do not work. 
        On a time series, I have verified that there is a artificial {slope_direction} slope in between 10/2015 and 10/2016 because of the ICD9 to ICD10 code switch. 
        {comment} Here are the codes that I've tried already: {codes}. 
        Please generate a new set of comma-separated codes for me.
        """

        print(f"THIS IS A SUPPLEMENTARY PROMPT: {supplementary_prompt}")

        raw_codes = get_concept(user_input_desc, supplementary_prompt)
        new_icd9_codes = parse_codes(raw_codes["icd9"])
        new_icd10_codes = parse_codes(raw_codes["icd10"])

        return {
            "name": "adjusted mapping",
            "icd9_codes": set(new_icd9_codes),
            "icd10_codes": set(new_icd10_codes),
        }

    # CASE 2: GOOD CODE MAPPING
    else:
        assert not artificial_break
        print(f"Found a good mapping! {codes}")
        return {
            "name": "best mapping",
            "icd9_codes": (
                set(codes.get("icd9", [])) if isinstance(codes, dict) else set()
            ),
            "icd10_codes": (
                set(codes.get("icd10", [])) if isinstance(codes, dict) else set()
            ),
        }
