"""Read every document in a sample folder and have the model fill in that sample's form.

Built on the same ideas as zenrows-example/extract.py: structured outputs give typed records,
every value comes with a quote from the document, and results are saved one document at a time,
so a stopped run carries on where it left off without paying twice.

Run it as `python extract.py oyster_payroll_changes`.
"""

import importlib
import json
import sys
from pathlib import Path

from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError
from pydantic_settings import BaseSettings, SettingsConfigDict
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

HERE = Path(__file__).parent
SAMPLES = HERE / "samples"
DOCUMENT_TYPES = (".txt", ".eml")


class Settings(BaseSettings):
    """Read from environment variables or the .env file at the top of the repo."""

    model_config = SettingsConfigDict(env_file=HERE.parent / ".env", extra="ignore")

    openai_api_key: str
    llm_model: str = "gpt-5.6-luna"


# The rules every sample shares. Each sample's schema.py adds its own INSTRUCTIONS.
RULES = """You read one operations document (an email, a forwarded thread, a note or a text
export) and turn it into records.

Rules:
- A document can hold several records, or none. If it holds none, return an empty list.
- Use only what the document says. If a value is not there, use null. Never guess.
- Every value you fill in needs its matching _quote field: the shortest piece of the document
  that states the value, copied character for character. If a value is null, its quote is null.
- If the document corrects itself, use the corrected value and quote the correction.
- Write dates as YYYY-MM-DD. If a date has no year, take the year from the rest of the document.
- Set needs_human to true, with a one-line reason, when a person should check the record before
  it is used: two possible values for one field, a value that is only in a missing attachment,
  numbers that disagree, or anything else you are unsure about. Otherwise use false and null.
"""

# Only retry errors that are likely to go away. A bad request would fail every time.
RETRYABLE = (APIConnectionError, APITimeoutError, RateLimitError)


class EmptyReply(Exception):
    """The model answered but gave no usable data, for example because it refused."""


def load_sample(name: str):
    """Return the sample's schema module and its folder."""
    folder = SAMPLES / name
    if not (folder / "schema.py").exists():
        available = ", ".join(sorted(path.name for path in SAMPLES.iterdir() if path.is_dir()))
        sys.exit(f"No sample called {name!r}. Choose one of: {available}")
    schema = importlib.import_module(f"samples.{name}.schema")
    return schema, folder


def read_documents(folder: Path) -> dict[str, str]:
    """Return {file name: text} for every document in the sample, in file name order."""
    documents = {}
    for path in sorted((folder / "documents").iterdir()):
        if path.suffix in DOCUMENT_TYPES:
            documents[path.name] = path.read_text(encoding="utf-8")
    return documents


def read_jsonl(path: Path) -> list[dict]:
    """Read a file with one JSON object per line. A missing file means nothing saved yet."""
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as file:
        return [json.loads(line) for line in file]


@retry(
    retry=retry_if_exception_type(RETRYABLE),
    wait=wait_exponential(min=2, max=30),
    stop=stop_after_attempt(5),
)
def extract_one(client: OpenAI, model: str, prompt: str, form, text: str):
    """Send one document to the model. Returns the filled-in form and the tokens used."""
    response = client.responses.parse(
        model=model,
        reasoning={"effort": "none"},
        input=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ],
        text_format=form,
    )
    if response.output_parsed is None:
        raise EmptyReply
    return response.output_parsed, response.usage.total_tokens


def run(sample: str) -> None:
    schema, folder = load_sample(sample)
    output = folder / "output"
    output.mkdir(exist_ok=True)
    out_file = output / "extractions.jsonl"

    documents = read_documents(folder)
    done = {row["document"] for row in read_jsonl(out_file)}
    todo = [name for name in documents if name not in done]
    print(f"{sample}: {len(done)} documents already done, {len(todo)} to go")
    if not todo:
        return

    settings = Settings()
    client = OpenAI(api_key=settings.openai_api_key, timeout=90)
    prompt = RULES + "\n" + schema.INSTRUCTIONS

    with out_file.open("a", encoding="utf-8") as out:
        for name in todo:
            # The file name is not sent, only the text, so the name can't hint at the answer.
            try:
                result, tokens = extract_one(
                    client, settings.llm_model, prompt, schema.Extraction, documents[name]
                )
            except Exception as error:  # noqa: BLE001 - one bad document should not stop the run
                print(f"  {name} failed: {type(error).__name__}")
                continue
            row = {
                "document": name,
                "tokens": tokens,
                "records": [record.model_dump(mode="json") for record in result.records],
            }
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
            print(f"  {name}: {len(row['records'])} records, {tokens} tokens")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python extract.py <sample name>")
    run(sys.argv[1])
