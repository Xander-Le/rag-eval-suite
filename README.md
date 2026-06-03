# Eval Suite for the WAB Filings RAG
**Defining and measuring "good" for an AI system — the part that's a product decision, not an engineering one.** A graded test suite that runs against the [WAB Filings RAG](https://github.com/Xander-Le/rag-wab-filings), scores every answer, and produces a regression report that diagnoses failures and ranks fixes by impact.

> **What this demonstrates as an AI PM:** the single most important AI PM skill — turning a vague "does it work?" into a measurable, repeatable answer. Choosing what to test, deciding what counts as correct, separating real system bugs from flaws in the measurement itself, validating a fix before claiming it, and prioritizing remediation. This is the same loop a model-risk function (SR 11-7) runs on any model a regulated bank deploys.

## The problem
Project 2 (the RAG system) could answer questions fluently. But "it seems to work when I try it" is not a quality bar anyone can ship behind — especially in finance, where a confident wrong figure is worse than a refusal. Project 2's own roadmap flagged the gap: *"No evaluation harness yet."* This repo closes it.

The product requirement isn't "test the chatbot." It's "make quality observable" — so regressions are caught before a user sees them, and so the team can argue about *what good means* with evidence instead of vibes. Defining that bar is the PM's job; engineers can build the harness, but coverage of edge cases, acceptable error rates, and what counts as a false positive are product calls.

## What it does
Runs a graded set of test cases against the RAG system, scores each with the method appropriate to the question type, writes a timestamped CSV, and reports pass rates by category. The accompanying [REGRESSION_REPORT.md](REGRESSION_REPORT.md) turns those numbers into prioritized product decisions.

## Product decisions (the interesting part)
This is where the project reads as PM work, not just a test script:

- **A deliberate test taxonomy, weighted on purpose.** 16 cases across happy-path (10), edge (3), and adversarial (3). The suite is weighted toward defensive behavior because in a financial-filings context a confident wrong answer is far costlier than an honest "I don't know."
- **Three scoring methods, each chosen for a reason.** Exact-match (numeric-aware) for factual recall, an LLM-as-judge rubric for open-ended and adversarial answers where there's no single correct string, and human review reserved for borderline high-stakes cases. Knowing which to use where is the PM call.
- **Separating system bugs from eval bugs.** Of 4 baseline failures, 2 were genuine retrieval failures and 2 were defects in the eval itself (a brittle matcher, an ambiguous question). Fixing what the eval owns — and saying so — is what makes the remaining failures trustworthy.
- **Hypotheses are tested, not assumed.** The obvious fix ("just retrieve more passages") was tested and rejected before it reached the report, which redirected the top recommendation to document processing.

## How it works
**Test cases** (`test_cases.py`) — each case carries a question, a category, a scoring method, and what "correct" means.
**Scoring** (`run_eval.py`, `judge.py`) — exact-match and refusal checks run locally; rubric cases call Claude as a judge.
**Run** — loop over every case → query the RAG → score → write CSV → print pass rates by category.

To make the RAG testable, its query logic was pulled out of the Streamlit UI into an importable `answer_question()` function — a small refactor that's the difference between a demo and a system you can put under test.

## Results
**75% baseline → 88%** after correcting two eval-quality defects. The two remaining failures are genuine system bugs (the retriever surfaces footnote tables over the MD&A summary; source text was extracted with fragmented numbers). Full diagnosis, the tested-and-rejected hypothesis, and the top-3 ranked fixes are in [REGRESSION_REPORT.md](REGRESSION_REPORT.md).

## Stack
- **Claude (Sonnet)** — LLM-as-judge for rubric scoring
- **Python stdlib** (`csv`, `re`) — deterministic exact-match and refusal scoring; no heavy deps
- **Targets** the [rag-wab-filings](https://github.com/Xander-Le/rag-wab-filings) RAG system via its `answer_question()` entry point

## Run it
1. The suite calls the RAG system, so it runs in that project's environment (which has the retrieval stack):
```bash
   ~/rag-wab-filings/venv/bin/python run_eval.py
```
2. Add your key to a `.env` file: `ANTHROPIC_API_KEY=...`
3. Results are written to `results/run_<timestamp>.csv`.

## Limitations and roadmap
- **16 cases proves the framework, not the score.** Expanding to ~60–80 cases (segment data, capital ratios, more adversarial variants) would make each category's pass rate statistically meaningful.
- **`must_cite` is currently weak** — it checks that *a* source was retrieved, not that the answer grounds itself in a cited figure. Enforcing real inline citations is the next scoring upgrade.
- **Single-system today; designed to be portable.** The same harness is intended to run against the [Payment Rail Agent](https://github.com/Xander-Le/payment-rail-agent) with tool-selection scoring — demonstrating the framework is a reusable asset, not a one-off.
