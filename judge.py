# judge.py — uses a strong model (Sonnet) to score open-ended answers
import json, anthropic
from dotenv import load_dotenv

load_dotenv()                 # reads ANTHROPIC_API_KEY from .env
client = anthropic.Anthropic()

JUDGE_PROMPT = """You are scoring an AI assistant's answer against a rubric.

Rubric: {rubric}
Question: {question}
Answer: {answer}

Decide if the answer satisfies the rubric. Reply with ONLY a JSON object,
no other text: {{"pass": true or false, "reason": "one short sentence"}}"""

def rubric_score(question, answer, rubric):
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content":
            JUDGE_PROMPT.format(rubric=rubric, question=question, answer=answer)}],
    )
    text = msg.content[0].text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"pass": False, "reason": "judge returned non-JSON: " + text[:80]}
