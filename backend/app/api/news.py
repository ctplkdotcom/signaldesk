from fastapi import APIRouter, HTTPException, Query

from app.services.news_service import NewsService

router = APIRouter()
news_service = NewsService()


@router.get("")
async def list_news(
    ticker: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
):
    articles = await news_service.get_news(ticker=ticker, limit=limit, offset=offset)
    return {"items": articles, "total": len(articles)}


@router.get("/{news_id}")
async def get_news_detail(news_id: int):
    article = await news_service.get_article(news_id)
    if not article:
        raise HTTPException(status_code=404, detail="News article not found")
    return article


@router.post("/ingest")
async def ingest_news(ticker: str | None = Query(None)):
    return {"status": "ok", "message": f"Ingestion triggered for ticker={ticker or 'all'}"}

@router.post("")
async def create_news(
    title: str,
    body: str | None = None,
    url: str | None = None,
    source: str | None = None,
    event_type: str | None = None,
    ticker: str | None = Query(None),
):
    result = await news_service.store_article(
        title=title,
        body=body,
        url=url,
        source=source,
        event_type=event_type,
        ticker=ticker,
    )
    return result
