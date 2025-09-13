ellyse - heeseung bias

evelyn - jay bias

neethi - heeseung bias

PIPELINE:
1. Generate a hypothesis mapping (using LLM) from the user prompt (and store it)
2. Plot as a time series
3. Evaluate the hypothesis using the statistical Chow test on the time series:
4. If hypothesis is valid, return hypothesis mapping
5. Else hypothesis is invalid, refine the hypothesis (go back to step 1 with an updated LLM prompt)
