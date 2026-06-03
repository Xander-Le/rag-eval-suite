# rag-eval-suite

An evaluation suite for the [WAB Filings RAG system](https://github.com/Xander-Le/rag-wab-filings).
Defining what "good" means for an AI system is a product decision — this repo is where
those decisions get written down, scored, and tracked over time.

## What it does
Runs a graded set of test cases against the RAG system, scores each with the
appropriate method, writes a timestamped CSV, and reports pass rates by category.

## Test taxonomy (16 cases)
- **Happy path (10)** — factual Q&A with known answers pulled from the FY2025 10-K.
- **Edge case (3)** — questions the filing can't answer; the system should refuse, not hallucinate.
- **Adversarial (3)** — loaded premises, prompt-injection, and off-topic asks.

The suite is deliberately weighted toward edge cases: in a financial-filings context,
a confident wrong answer is far costlier than an honest "I don't know."

## Scoring methods
- **Exact-match** — numeric-aware comparison for factual questions (fast, repeatable).
- **LLM-as-judge** — a Sonnet rubric grader for open-ended/adversarial answers.
- **Human review** — reserved for borderline high-stakes cases.

## Latest results
75% baseline → 88% after correcting two eval-quality defects. Full diagnosis,
ranked fixes, and before/after in [REGRESSION_REPORT.md](REGRESSION_REPORT.md).

## Run it
```bash
python run_eval.py   # uses the rag-wab-filings environment; see the report for details
```
