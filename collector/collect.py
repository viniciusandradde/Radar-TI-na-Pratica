"""Collect public RSS/Atom feeds and insert source-linked items into Supabase.
No scraping of paywalled pages, social networks, or newsletter content.
"""
from __future__ import annotations
import json, os, re, sys, hashlib
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urldefrag, urlparse
import feedparser
import httpx
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from supabase import create_client

ROOT = os.path.dirname(__file__)
USER_AGENT = "VSA-Radar/1.0 (+https://github.com/viniciusandradde/Radar-TI-na-Pratica-)"
TIMEOUT = 18

def clean_url(url: str) -> str:
    url = urldefrag((url or "").strip())[0]
    return re.sub(r"[?&](utm_[^=]+|fbclid|gclid)=[^&]*", "", url).rstrip("?&")

def discover_feed(client: httpx.Client, homepage: str) -> str | None:
    try:
        response = client.get(homepage, follow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.find_all("link", href=True):
            rel = " ".join(link.get("rel", [])).lower()
            typ = (link.get("type") or "").lower()
            if "alternate" in rel and ("rss" in typ or "atom" in typ or "xml" in typ):
                return urljoin(str(response.url), link["href"])
        # Conservative common feed paths only; validate by parsing before accepting.
        base = f"{urlparse(str(response.url)).scheme}://{urlparse(str(response.url)).netloc}"
        for suffix in ("/feed/", "/feed", "/rss", "/rss.xml", "/atom.xml"):
            candidate = urljoin(base, suffix)
            parsed = feedparser.parse(candidate)
            if parsed.entries:
                return candidate
    except Exception as exc:
        print(f"[WARN] discovery failed for {homepage}: {exc}")
    return None

def parse_date(entry):
    for key in ("published", "updated", "created"):
        value = entry.get(key)
        if value:
            try:
                dt = date_parser.parse(value)
                if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc).isoformat()
            except Exception:
                pass
    return datetime.now(timezone.utc).isoformat()

def summarize(entry):
    raw = entry.get("summary") or entry.get("description") or ""
    text = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text)[:700]

def main():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    owner_id = os.environ.get("VSA_OWNER_ID")
    if not all((url, key, owner_id)):
        sys.exit("Missing SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY or VSA_OWNER_ID")
    supabase = create_client(url, key)
    with open(os.path.join(ROOT, "sources.json"), encoding="utf-8") as f:
        sources = json.load(f)
    headers = {"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, text/html"}
    inserted = skipped = errors = 0
    with httpx.Client(headers=headers, timeout=TIMEOUT) as client:
        for source in sources:
            if not source.get("enabled", True): continue
            homepage = source["homepage_url"]
            feed_url = source.get("feed_url") or discover_feed(client, homepage)
            if not feed_url:
                print(f"[SKIP] no RSS/Atom discovered: {source['name']}")
                skipped += 1
                continue
            parsed = feedparser.parse(feed_url)
            if parsed.bozo and not parsed.entries:
                print(f"[WARN] invalid feed {source['name']}: {parsed.bozo_exception}")
                errors += 1
                continue
            print(f"[FEED] {source['name']} -> {feed_url} ({len(parsed.entries)} entries)")
            for entry in parsed.entries[:25]:
                title = (entry.get("title") or "").strip()
                link = clean_url(entry.get("link") or "")
                if not title or not link or urlparse(link).scheme not in ("http", "https"): continue
                record = {
                    "owner_id": owner_id,
                    "source_name": source["name"],
                    "source_url": homepage,
                    "canonical_url": link,
                    "title": title[:500],
                    "summary": summarize(entry),
                    "published_at": parse_date(entry),
                    "category": source.get("category", "Mercado & Estratégia"),
                    "status": "new"
                }
                try:
                    # Unique(owner_id, canonical_url) makes repeated runs idempotent.
                    supabase.table("news_items").upsert(record, on_conflict="owner_id,canonical_url", ignore_duplicates=True).execute()
                    inserted += 1
                except Exception as exc:
                    print(f"[ERROR] {source['name']} / {title[:80]}: {exc}")
                    errors += 1
    print(f"Finished. processed={inserted} undiscovered={skipped} errors={errors}")

if __name__ == "__main__":
    main()
