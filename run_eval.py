# run_eval.py — runs every test case against the RAG system and scores it
import os, sys, csv, re, datetime
sys.path.insert(0, os.path.expanduser("~/rag-wab-filings"))

from test_cases import RAG_CASES
from judge import rubric_score
from rag_core import answer_question

REFUSAL_CUES = ["don't know", "do not know", "not contain", "cannot",
                "isn't in", "is not in", "no information", "unable to",
                "not provided", "not stated", "not available",
                "don't have enough", "do not have enough"]

def matches(answer, expected):
    a = answer.lower().replace(",", "")
    e = expected.lower().replace(",", "")
    if e in a:                                  # plain substring
        return True
    m = re.match(r"\$?([0-9]+(?:\.[0-9]+)?)", e.strip())   # numeric-aware
    if m:
        num = m.group(1)
        for an in re.findall(r"[0-9]+(?:\.[0-9]+)?", a):
            if an == num or an.startswith(num + "."):       # 63.3 ~ 63
                return True
    return False

def score_case(case, answer, sources):
    if case["scoring"] == "exact_match":
        ok = any(matches(answer, e) for e in case["expected"])
        if case.get("must_cite") and not sources:
            ok = False
        return ok, "exact_match"
    if case["scoring"] == "refusal":
        a = answer.lower()
        return any(c in a for c in REFUSAL_CUES), "refusal"
    if case["scoring"] == "rubric":
        v = rubric_score(case["question"], answer, case["rubric"])
        return bool(v["pass"]), "rubric: " + v["reason"]
    return False, "unknown"

def main():
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    rows = []
    for case in RAG_CASES:
        answer, sources = answer_question(case["question"])
        ok, note = score_case(case, answer, sources)
        rows.append([case["id"], case["category"], ok, note, answer[:200]])
        print(f"{case['id']:7} {'PASS' if ok else 'FAIL'}  {case['category']}")
    os.makedirs("results", exist_ok=True)
    path = f"results/run_{stamp}.csv"
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id","category","pass","note","answer_preview"]); w.writerows(rows)
    total = len(rows); passed = sum(1 for r in rows if r[2])
    print(f"\nOVERALL: {passed}/{total} passed ({100*passed/total:.0f}%)")
    cats = {}
    for r in rows:
        cats.setdefault(r[1], [0,0]); cats[r[1]][1]+=1
        if r[2]: cats[r[1]][0]+=1
    print("BY CATEGORY:")
    for c,(p,t) in cats.items(): print(f"  {c:13} {p}/{t} ({100*p/t:.0f}%)")
    print(f"\nSaved: {path}")

if __name__ == "__main__":
    main()
