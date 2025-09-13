from google import genai
import os
from dotenv import load_dotenv
from google.genai import types
import time
import google.api_core.exceptions

# Load environment variables from .env file at the project root
load_dotenv()


def prompt_llm(prompt: str):
    """
    Prompts the Gemini model, with Google Search enabled for grounding.
    Includes exponential backoff to handle API rate limits.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "API key not found. Please set the GEMINI_API_KEY environment variable."
        )
    else:
        print("USING REAL MODEL!!!")
        print(f"PROMPT: {prompt}")  # Print a snippet of the prompt

    client = genai.Client(api_key=api_key)
    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    config = types.GenerateContentConfig(tools=[grounding_tool])
    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt, config=config
    )

    # catch too many retries so it doesn't crash
    retries = 3
    delay = 2
    for i in range(retries):
        try:
            # The 'tools' parameter is now part of the model, not the generate_content call
            response = client.models.generate_content(prompt)
            return response.text
        except google.api_core.exceptions.ResourceExhausted as e:
            if i < retries - 1:
                print(f"Rate limit exceeded. Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2
            else:
                print("Rate limit exceeded. Max retries reached.")
                raise e

    return ""

    # response = """ICD9: 30420, 30421, 30422, 30423, 30560, 30561, 30562, 30563, 76075, 97081
    # ICD10: F1410, F1411, F14120, F14121, F14122, F14129, F1414, F14150, F14151, F14159,F14180,F14181, F14182, F14188,F1419,F1420,
    #     F1421,
    #     F14220,
    #     F14221,
    #     F14222,
    #     F14229,
    #     F1423,
    #     F1424,
    #     F14250,
    #     F14251,
    #     F14259,
    #     F14280,
    #     F14281,
    #     F14282,
    #     F14288,
    #     F1429,
    #     F1490,
    #     F14920,
    #     F14921, F14922
    #     F14929, F1494
    #     F14950, F14951
    #     F14959, F14980
    #     F14981, F14982
    #     F14988, F1499, P0441"""
    # print(f"USING THE FOLLOWING MOCK (VALID) MAPPING: {response}")
    # print(f"FULL PROMPT TO LLM: {prompt}")
    # response = "ICD9: 4250, 42511, 42518, 4252, 4253, 4254, 4255, 4257, 4258, 4259\nICD10: I420, I421, I422, I423, I424, I425, I426, I427, I428"
    # print("USING THE FOLLOWING MOCK (BAD) MAPPING:")
    # return response
