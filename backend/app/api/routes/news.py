from datetime import datetime, timedelta
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

from fastapi import APIRouter, HTTPException, status


router = APIRouter(tags=["news"])

NEWS_CACHE: dict[str, object] = {"expires_at": datetime.min, "items": []}
NEWS_TTL = timedelta(minutes=15)
NEWS_SOURCE = "https://www.science.org/rss/news_current.xml"


def _fetch_news() -> list[dict]:
    try:
        with urllib.request.urlopen(NEWS_SOURCE, timeout=10) as response:
            data = response.read()
    except urllib.error.URLError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to reach news source: {exc.reason}",
        ) from exc

    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to parse news feed",
        ) from exc

    items: list[dict] = []
    for entry in root.findall(".//item")[:12]:
        title = (entry.findtext("title") or "").strip()
        link = (entry.findtext("link") or "").strip()
        published = (entry.findtext("pubDate") or "").strip()
        if not title or not link:
            continue
        items.append(
            {
                "title": title,
                "url": link,
                "published_at": published,
                "source": "Science.org",
            }
        )
    return items


@router.get("/news/trending")
def get_trending_news() -> dict:
    now = datetime.utcnow()
    expires_at = NEWS_CACHE.get("expires_at")
    if isinstance(expires_at, datetime) and expires_at > now:
        return {"items": NEWS_CACHE.get("items", [])}

    try:
        items = _fetch_news()
    except HTTPException:
        cached_items = NEWS_CACHE.get("items", [])
        if cached_items:
            return {"items": cached_items}
        raise

    NEWS_CACHE["items"] = items
    NEWS_CACHE["expires_at"] = now + NEWS_TTL
    return {"items": items}
