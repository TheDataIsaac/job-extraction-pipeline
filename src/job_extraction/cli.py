"""Command line entry point: jobs prepare, extract, analyze, index, ask, serve."""

import asyncio
from pathlib import Path

import typer

app = typer.Typer(help="Turn freelance job postings into structured data.", no_args_is_help=True)

RAW = Path("data/raw/freelancer_job_postings.csv")
POSTINGS = Path("data/postings.jsonl")
EXTRACTIONS = Path("data/extractions.jsonl")


@app.command()
def prepare() -> None:
    """Clean the raw CSV and remove duplicate postings."""
    from job_extraction.prepare import prepare as run

    rows, kept = run(RAW, POSTINGS)
    typer.echo(f"{rows} rows read, {kept} unique postings written to {POSTINGS}")


@app.command()
def extract(limit: int = typer.Option(None, help="Only process the first N postings.")) -> None:
    """Extract structured data with the model. Safe to stop and run again."""
    from job_extraction.extract import run_batch

    asyncio.run(run_batch(POSTINGS, EXTRACTIONS, limit))


@app.command()
def analyze() -> None:
    """Build the summary tables and charts from the extractions."""
    from job_extraction.analyze import run

    run(POSTINGS, EXTRACTIONS, Path("reports"))


@app.command()
def index() -> None:
    """Embed every posting so it can be searched by meaning (needed once, before `ask`)."""
    from job_extraction.ask import build_index

    typer.echo(f"{build_index(POSTINGS)} postings embedded")


@app.command()
def ask(
    question: str, k: int = typer.Option(8, help="How many postings to give the model.")
) -> None:
    """Answer a question about the postings, citing the ones used."""
    from job_extraction.ask import Asker

    answer, found = Asker(POSTINGS, EXTRACTIONS).ask(question, k)
    typer.echo(answer + "\n")
    for number, posting in enumerate(found, 1):
        typer.echo(f"[{number}] {posting['id']}  {posting['title'][:90]}")


@app.command()
def serve(port: int = 8000) -> None:
    """Run the extraction API."""
    import uvicorn

    uvicorn.run("job_extraction.api:app", port=port)
