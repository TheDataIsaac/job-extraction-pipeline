"""Ask questions about the postings: retrieve the closest postings by embedding, then answer from them with citations."""

import json
from pathlib import Path

import numpy as np
from openai import OpenAI

from job_extraction.extract import Settings

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDINGS = Path("data/embeddings.npy")  # one row per posting, in the order of postings.jsonl
BATCH = 100  # postings embedded per request

INSTRUCTIONS = """You answer questions about freelance job postings using only the numbered postings provided.
- Use only the postings. If they do not answer the question, say so.
- After each claim, give the number of the posting it came from, like [3].
- You only see a few postings, not the whole market. Never state totals or percentages for all postings.
- Be brief: a short paragraph or a few bullet points."""


def build_index(postings_file: Path) -> int:
    """Embed every posting and save the numbers. Takes a minute or two and costs a few cents."""
    client = OpenAI(api_key=Settings().openai_api_key)
    postings = [json.loads(line) for line in postings_file.open(encoding="utf-8")]
    texts = [f"{p['title']}\n{p['description'][:2000]}" for p in postings]

    vectors = []
    for start in range(0, len(texts), BATCH):
        response = client.embeddings.create(
            model=EMBEDDING_MODEL, input=texts[start : start + BATCH]
        )
        vectors.extend(item.embedding for item in response.data)
        print(f"{len(vectors)}/{len(texts)}")
    np.save(EMBEDDINGS, np.array(vectors, dtype=np.float32))
    return len(vectors)


class Asker:
    def __init__(self, postings_file: Path, extractions_file: Path) -> None:
        if not EMBEDDINGS.exists():
            raise SystemExit("No embeddings yet. Run:  uv run jobs index")
        self.client = OpenAI(api_key=Settings().openai_api_key)
        self.model = Settings().llm_model
        self.postings = [json.loads(line) for line in postings_file.open(encoding="utf-8")]
        extractions = (json.loads(line) for line in extractions_file.open(encoding="utf-8"))
        self.facts = {record["id"]: record["data"] for record in extractions}
        vectors = np.load(EMBEDDINGS)
        self.vectors = vectors / np.linalg.norm(
            vectors, axis=1, keepdims=True
        )  # length 1, so a dot product is cosine

    def retrieve(self, question: str, k: int = 8) -> list[dict]:
        """The k postings closest in meaning to the question."""
        response = self.client.embeddings.create(model=EMBEDDING_MODEL, input=question)
        question_vector = np.array(response.data[0].embedding, dtype=np.float32)
        question_vector /= np.linalg.norm(question_vector)
        best = np.argsort(-(self.vectors @ question_vector))[:k]
        return [self.postings[i] for i in best]

    def ask(self, question: str, k: int = 8) -> tuple[str, list[dict]]:
        """Retrieve, then answer from the retrieved postings. Returns the answer and the postings it was given."""
        found = self.retrieve(question, k)
        blocks = []
        for number, posting in enumerate(found, 1):
            facts = self.facts[posting["id"]]
            blocks.append(
                f"[{number}] {posting['title']}\n{posting['description'][:700]}\n"
                f"(extracted: {facts['project_type']}, tools {facts['tools']}, budget {facts['stated_budget']}, "
                f"timeline {facts['timeline_days']} days)"
            )
        response = self.client.responses.create(
            model=self.model,
            reasoning={"effort": "none"},
            instructions=INSTRUCTIONS,
            input=f"Question: {question}\n\nPostings:\n\n" + "\n\n".join(blocks),
        )
        return response.output_text, found
