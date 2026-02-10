from datetime import datetime, timedelta
import json
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from fastapi import APIRouter, HTTPException, Query, status


router = APIRouter(tags=["conferences"])

CONFERENCE_CACHE: dict[str, dict[str, object]] = {}
CONFERENCE_TTL = timedelta(minutes=30)
WIKICFP_RSS = "https://www.wikicfp.com/cfp/rss"
OPENALEX_SOURCES = "https://api.openalex.org/sources"


def _fetch_feed(url: str) -> bytes:
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.read()
    except urllib.error.URLError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to reach conference source: {exc.reason}",
        ) from exc


def _parse_field(text: str, label: str) -> str:
    for line in text.splitlines():
        if line.strip().lower().startswith(label.lower()):
            return line.split(":", 1)[-1].strip()
    return ""


def _parse_feed(data: bytes) -> list[dict]:
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to parse conference feed",
        ) from exc

    items: list[dict] = []
    for entry in root.findall(".//item"):
        title = (entry.findtext("title") or "").strip()
        link = (entry.findtext("link") or "").strip()
        description = (entry.findtext("description") or "").strip()
        if not title or not link:
            continue
        conference_date = _parse_field(description, "When") or "TBA"
        deadline = _parse_field(description, "Deadline") or "TBA"
        location = _parse_field(description, "Where") or ""
        items.append(
            {
                "title": title,
                "url": link,
                "conference_date": conference_date,
                "submission_deadline": deadline,
                "location": location,
                "source": "WikiCFP",
            }
        )
    return items


def _fetch_openalex(keyword: str) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "filter": f"type:conference,display_name.search:{keyword}",
            "sort": "works_count:desc",
            "per-page": 20,
        }
    )
    data = _fetch_feed(f"{OPENALEX_SOURCES}?{params}")
    payload = json.loads(data.decode("utf-8"))
    results = payload.get("results", [])
    items: list[dict] = []
    for entry in results:
        title = entry.get("display_name")
        url = entry.get("homepage_url") or entry.get("id")
        if not title or not url:
            continue
        location = entry.get("country_code") or ""
        items.append(
            {
                "title": title,
                "url": url,
                "conference_date": "Check website",
                "submission_deadline": "Check website",
                "location": location,
                "source": "OpenAlex",
            }
        )
    return items


@router.get("/conferences")
def get_conferences(
    keyword: str = Query("research", min_length=2, max_length=60),
) -> dict:
    now = datetime.utcnow()
    cache = CONFERENCE_CACHE.get(keyword)
    if cache and cache.get("expires_at") and cache["expires_at"] > now:
        return {"items": cache.get("items", [])}

    query = urllib.parse.urlencode({"keyword": keyword})
    try:
        data = _fetch_feed(f"{WIKICFP_RSS}?{query}")
        items = _parse_feed(data)
    except HTTPException as exc:
        cached_items = cache.get("items", []) if cache else []
        if cached_items:
            return {"items": cached_items, "warning": str(exc.detail)}
        try:
            items = _fetch_openalex(keyword)
            return {
                "items": items[:30],
                "warning": "WikiCFP is unavailable. Showing OpenAlex conference sources.",
            }
        except Exception:
            return {
                "items": [],
                "warning": "Conference feed is temporarily unavailable.",
            }

    CONFERENCE_CACHE[keyword] = {
        "items": items[:30],
        "expires_at": now + CONFERENCE_TTL,
    }
    return {"items": items[:30]}
