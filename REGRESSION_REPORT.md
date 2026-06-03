# Regression Report — WAB Filings RAG Eval Suite

**System under test:** `rag-wab-filings` (RAG over Western Alliance's FY2025 10-K)
**Eval suite:** `rag-eval-suite` — 16 test cases (10 happy-path, 3 edge, 3 adversarial)
**Author:** Xander Le · **Date:** June 2, 2026

---

## Executive summary

I built an eval suite of 16 graded test cases over the WAB filings RAG system and ran it twice: once as a baseline, and again after fixing defects I found in the eval itself. The baseline scored **75% (12/16)**. After correcting two eval-quality issues, the suite scored **88% (14/16)**.

The headline is not the number — it's the diagnosis. Of the four baseline failures, two were genuine system bugs (the retriever surfaces dense footnote tables instead of the management-discussion summary, and the source text was extracted with fragmented numbers), and two were defects in my own eval (a brittle scoring comparison and an ambiguously worded question). I fixed the two I owned and re-ran to confirm; the two system bugs remain and are this report's top recommendation.

---

## Results by category

| Category | Baseline | After eval fixes | Read |
|---|---|---|---|
| Happy path | 6/10 (60%) | 8/10 (80%) | Factual recall is the weak spot — driven by retrieval, not the model |
| Edge case | 3/3 (100%) | 3/3 (100%) | Correctly refuses unanswerable questions instead of hallucinating |
| Adversarial | 3/3 (100%) | 3/3 (100%) | Resists loaded premises, injection, and off-topic asks |
| **Overall** | **12/16 (75%)** | **14/16 (88%)** | |

The system is trustworthy where it matters most defensively (it says "I don't know" rather than inventing answers, and it doesn't take the bait on adversarial prompts). Its remaining weakness is purely in retrieving the right passage for factual questions.

---

## Where it still fails (the 2 genuine system bugs)

Both remaining failures are the same root cause: the relevant fact exists in the filing but is never retrieved.

**HP-01 — "What was WAB's total net revenue for FY2025?"**
System answered: *"Based on the provided context, I don't have enough information to answer this question."*
The fact ("Net revenue of $3.5 billion") is in the filing's MD&A highlights, but inspection of the retrieved passages showed all of them were balance-sheet footnote tables (deposits, related-party balances, charge-offs, goodwill). The summary section was never surfaced.

**HP-04 — "What was WAB's year-over-year net revenue growth in 2025?"**
System answered: *"The provided context does not contain information about WAB's total net revenue figures..."*
Same passage, same miss. The "12.0% growth, $380.9 million" line sits in the same un-retrieved highlights section.

**A rejected hypothesis (documented on purpose):** I first assumed the fix was simply retrieving more passages, and tested it by raising top-k from 4 to 8. It did **not** fix HP-01 — the highlights passage still didn't rank into the top 8, and the retrieved sources also revealed that figures were extracted as fragmented tokens (e.g. `$ \n 5.4 \n billion`). The problem is upstream of retrieval depth, in document processing.

---

## Top 3 fixes, ranked by impact

**1. Re-process and re-chunk the source document.** *(Highest impact — addresses both remaining failures.)*
The 10-K was extracted into text that splits dollar amounts across lines and chops the MD&A summary in a way that doesn't embed well. Re-extract with layout-aware parsing and re-chunk with sentence-aware splitting (and overlap) so the revenue-highlights section becomes a coherent, retrievable unit. This is the single change most likely to move happy-path accuracy.

**2. Add inline-citation enforcement to the scoring.** *(Medium impact — hardens the eval and the product.)*
The current `must_cite` check only verifies that *some* source was retrieved, which is always true in this RAG. It should verify the answer actually grounds itself in a cited figure. Strengthening this catches "right number, no grounding" cases the suite currently lets pass.

**3. Expand the suite to ~60–80 cases.** *(Compounding impact — more signal, less noise.)*
Sixteen cases is enough to prove the framework; it's too few to trust a single percentage. Add more happy-path facts (segment data, capital ratios, risk factors) and more adversarial variants so each category's score is statistically meaningful and regressions are easier to localize.

---

## Fixes already applied this cycle (validated before/after)

To distinguish system bugs from eval bugs, I corrected the two failures that were my eval's fault and re-ran to confirm the improvement was real:

- **Numeric-aware scoring (HP-10).** The system correctly answered "approximately **63.3%**," but my exact-match list only contained "63%," so a correct answer was scored as a failure. I replaced the strict substring check with a numeric-aware match (`63.3` now matches an expected `63`). **Result: HP-10 FAIL → PASS.**
- **Disambiguated an ambiguous case (HP-07).** My question ("how much in CRE office loans") had two valid answers in the filing — "$2.1B / 3.7% of total loans HFI" and "4% of CRE loans." I rewrote it to pin the denominator ("...as a percentage of total loans held for investment"). **Result: HP-07 FAIL → PASS.**

Combined, these moved the measured score from **75% → 88%** — and, more importantly, made the two remaining failures *true* failures worth fixing.

---

## What I'd do next

Implement fix #1 (re-chunking) in a copy of the index, re-run this suite, and report the new happy-path pass rate against the 80% baseline recorded here. Then expand the suite and wire it to run on every change to the RAG system so regressions are caught before they reach a user — the same monitoring discipline a model-risk function (SR 11-7) would expect for a deployed model.
