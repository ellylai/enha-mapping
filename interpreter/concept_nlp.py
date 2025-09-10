USER_INPUT_DESC = "cardiovascular diseases"
MODEL = ...

def load_model_function(MODEL):
    pass


def get_concept(USER_INPUT_DESC: str) -> list[str]:
    # load llm model
    llm = load_model_function(MODEL) # need to write this

    # parse USER_INPUT_DESC
    extraction_prompt = f"""
        You are a clinical terminology expert. Analyze the following description and extract the primary clinical concepts.
        Description: "{USER_INPUT_DESC}"
        ---
        Return only the core concepts as a comma-separated list.
        """
    # get key clinical terms
    # The llm.invoke method is a placeholder for your model's actual inference function
    key_terms_str = llm.invoke(extraction_prompt)
    key_terms = [term.strip() for term in key_terms_str.split(',') if term.strip()]

    if not key_terms:
        return []
    
    # expand on key clinical terms
    expansion_prompt = f"""
    You are a clinical terminology expert. Given a list of core medical terms, expand it with synonyms, common sub-types, and closely related concepts.
    Core Terms: "{', '.join(key_terms)}"
    ---
    Return a comma-separated list of these additional terms. Do not repeat the original core terms.
    """
    extras_str = llm.invoke(expansion_prompt)
    extras = [term.strip() for term in extras_str.split(',') if term.strip()]
    category = key_terms + extras

    seen = set()
    return [x for x in category if not (x in seen or seen.add(x))]
