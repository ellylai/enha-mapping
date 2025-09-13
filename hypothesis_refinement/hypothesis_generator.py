# CORE LOGIC IS HERE. KEEP WORKING...

import pandas as pd
import typing
from .icd_parsing_script import icd_map, parse_codes
from interpreter.prompt_handler import get_concept

Hypothesis = typing.TypedDict(
    "Hypothesis", {"name": str, "icd9_codes": set[str], "icd10_codes": set[str]}
)


def generate_hypotheses(
    history: list[dict],
    prev_results: dict,
    user_input_desc="",
) -> Hypothesis:

    # BASE CASE: NO CODES GENERATED YET -> GENERATE NAIVE CODES
    if history == []:
        raw_codes = get_concept(user_input_desc)
        naive_icd9_codes = parse_codes(raw_codes["icd9"])
        naive_icd10_codes = parse_codes(raw_codes["icd10"])
        print(f"Extracted {len(naive_icd9_codes)} ICD-9: {naive_icd9_codes}")
        print(f"Extracted {len(naive_icd10_codes)} ICD-10: {naive_icd10_codes}")

        return {
            "name": "naive mapping",
            "icd9_codes": set(naive_icd9_codes),
            "icd10_codes": set(naive_icd10_codes),
        }
    # CASE 1: BAD CODE MAPPING -> GENERATE HYPOTHESIS
    elif prev_results["artificial_break"]:

        truncated_history = []
        for results in history:
            truncated_results = {
                "hypothesis": results["hypothesis"],
                "artificial_slope": results["artificial_slope"],
                "comment": results["comment"],
            }
            truncated_history.append(truncated_results)
        supplementary_prompt = f"""
        You have already generated some mappings for me, but the following mappings for "{user_input_desc}" do not work. 
        Here are the code sets that I've tried already, so DO NOT generate a duplicate set of codes for me:
        {truncated_history}
        See the comment for each previously-generated set, and please generate a new set of comma-separated codes for me accordingly, as an expert with up-to-date web knowledge about ICD code usage.
        """

        raw_codes = get_concept(user_input_desc, supplementary_prompt)
        new_icd9_codes = parse_codes(raw_codes["icd9"])
        new_icd10_codes = parse_codes(raw_codes["icd10"])
        print(f"Extracted {len(new_icd9_codes)} ICD-9: {new_icd9_codes}")
        print(f"Extracted {len(new_icd10_codes)} ICD-10: {new_icd10_codes}")

        return {
            "name": "adjusted mapping",
            "icd9_codes": set(new_icd9_codes),
            "icd10_codes": set(new_icd10_codes),
        }

    # CASE 2: GOOD CODE MAPPING
    else:
        assert not prev_results["artificial_break"]
        curr_codes = history[-1]["hypothesis"]
        print(f"Found a good mapping! {curr_codes}")
        return {
            "name": "best mapping",
            "icd9_codes": (
                set(curr_codes.get("icd9", []))
                if isinstance(curr_codes, dict)
                else set()
            ),
            "icd10_codes": (
                set(curr_codes.get("icd10", []))
                if isinstance(curr_codes, dict)
                else set()
            ),
        }
