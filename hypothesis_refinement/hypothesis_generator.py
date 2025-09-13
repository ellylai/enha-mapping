# CORE LOGIC IS HERE. KEEP WORKING...

import pandas as pd
import typing
from llm_client import OllamaClient

Hypothesis = typing.TypedDict(
    "Hypothesis", {"name": str, "icd9_codes": set[str], "icd10_codes": set[str]}
)


def agentic_web_search(code: str) -> list[str]:
    """
    NOT IMPLEMENTED
    Placeholder for an agent that searches the web for clinical mappings.
    For now, it returns an empty list.
    """
    print(f"Agentic Web Search (mock): Searching for mappings for {code}...")
    # In a real implementation, this would use a search API and an LLM to find
    # and parse relevant clinical coding guidelines from the web.
    return []


def generate_hypotheses(naive_codes: dict, artificial_break: bool) -> list[Hypothesis]:
    """
    MOCK FUNCTION, NOT IMPLEMENTED
    Generates mapping hypotheses using GEM files and agentic search placeholders.
    """

    # BASE CASE: NO CODES GENERATED YET
    if not naive_codes:
        # GENERATE NAIVE CODES
        base_prompt = "Give me ONLY comma-separated ICD10 codes for cocaine abuse. Do not provide any other text response."
        response = OllamaClient.invoke(prompt=base_prompt)
        codes = [str(code).strip() for code in response.split(",")]
        print(f"Naive ICD10 codes generated: {codes}")

    # CASE 1: BAD CODE MAPPING
    elif artificial_break:
        new_prompt = ""

    # CASE 2: GOOD CODE MAPPING
    else:
        assert not artificial_break
