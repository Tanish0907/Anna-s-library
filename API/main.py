from fastapi import FastAPI, HTTPException, Query
from pydantic import HttpUrl
from AnnasLibrary import Scraper
app = FastAPI(title="Web Scraper API", version="1.0.0")


@app.get("/search")
def search(query: str):
    result = Scraper.Search(query)
    return result