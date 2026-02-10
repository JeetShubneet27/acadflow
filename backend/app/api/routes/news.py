from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

from fastapi import APIRouter, HTTPException, status


router = APIRouter(tags=["news"])

NEWS_CACHE: dict[str, object] = {"expires_at": datetime.min, "items": []}
NEWS_TTL = timedelta(minutes=15)
NEWS_SOURCES = [
    ("Science.org", "https://www.science.org/rss/news_current.xml"),
    ("Nature", "https://www.nature.com/nature.rss"),
    ("PNAS", "https://www.pnas.org/rss/CurrentIssue.xml"),
    ("arXiv (CS)", "https://export.arxiv.org/rss/cs"),
]


def _fetch_feed(source_url: str) -> bytes:
    try:
        with urllib.request.urlopen(source_url, timeout=10) as response:
            return response.read()
    except urllib.error.URLError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to reach news source: {exc.reason}",
        ) from exc


def _parse_feed(data: bytes, source_name: str) -> list[dict]:
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to parse {source_name} feed",
        ) from exc

    items: list[dict] = []
    for entry in root.findall(".//item"):
        title = (entry.findtext("title") or "").strip()
        link = (entry.findtext("link") or "").strip()
        published = (entry.findtext("pubDate") or "").strip()
        if not title or not link:
            continue
        published_dt = None
        if published:
            try:
                published_dt = parsedate_to_datetime(published)
            except (TypeError, ValueError):
                published_dt = None
        items.append(
            {
                "title": title,
                "url": link,
                "published_at": published,
                "source": source_name,
                "_published_at": published_dt,
            }
        )
    return items


def _fetch_news() -> list[dict]:
    items: list[dict] = []
    errors: list[str] = []

    for source_name, source_url in NEWS_SOURCES:
        try:
            data = _fetch_feed(source_url)
            items.extend(_parse_feed(data, source_name))
        except HTTPException as exc:
            errors.append(str(exc.detail))

    if not items:
        detail = "Unable to reach news sources."
        if errors:
            detail = f"{detail} {'; '.join(errors)}"
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)

    seen: set[str] = set()
    deduped: list[dict] = []
    for item in items:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        deduped.append(item)

    deduped.sort(
        key=lambda item: item.get("_published_at") or datetime.min,
        reverse=True,
    )
    for item in deduped:
        item.pop("_published_at", None)

    return deduped[:20]


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
