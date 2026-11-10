"""A small web API: send a posting, get structured data back."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from job_extraction.extract import EmptyReply, Extractor, Settings
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
    try:
        data, _ = await extractor.extract(posting.title, posting.description)
    except EmptyReply:
        raise HTTPException(status_code=502, detail="The model gave no usable answer.")
    return ExtractionOut(data=data, problems=check(data, posting.title + " " + posting.description))
