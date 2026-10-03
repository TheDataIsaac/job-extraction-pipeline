"""A small web API: send a posting, get structured data back."""

from fastapi import FastAPI
from pydantic import BaseModel, Field

from job_extraction.extract import Extractor, Settings
from job_extraction.schema import JobExtraction
from job_extraction.verify import check

app = FastAPI(title="Job extraction API")
extractor = Extractor(Settings())


class PostingIn(BaseModel):
    title: str = ""
    description: str = Field(min_length=20, max_length=10_000)


class ExtractionOut(BaseModel):
    data: JobExtraction
    problems: list[str]  # empty when every quote and number was found in the posting


@app.post("/extract", response_model=ExtractionOut)
async def extract(posting: PostingIn) -> ExtractionOut:
    data, _ = await extractor.extract(posting.title, posting.description)
    return ExtractionOut(data=data, problems=check(data, posting.title + " " + posting.description))
